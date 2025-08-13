from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import google.generativeai as genai
import os
from datetime import datetime
import re

# ==== Gemini API Config ====
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# ==== FastAPI App ====
app = FastAPI()

# Mount static files for CSS/JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# ==== Simple UI Route ====
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gemini SQL Chatbot</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <h1>Chat with the DB</h1>
        <div id="chat-box" style="border:1px solid #ccc; padding:10px; height:300px; overflow-y:auto;"></div>
        <input id="user-input" type="text" placeholder="Type a message..." style="width:80%;">
        <button onclick="sendMessage()">Send</button>

        <script>
        async function sendMessage() {
            let message = document.getElementById("user-input").value;
            if (!message) return;

            let chatBox = document.getElementById("chat-box");
            chatBox.innerHTML += "<p><b>You:</b> " + message + "</p>";

            let response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message })
            });

            let data = await response.json();
            chatBox.innerHTML += "<p><b>Bot:</b> " + data.reply + "</p>";
            document.getElementById("user-input").value = "";
            chatBox.scrollTop = chatBox.scrollHeight;
        }
        </script>
    </body>
    </html>
    """

# ==== Chat Endpoint ====
@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        user_message = body.get("message", "").strip()
        if not user_message:
            return JSONResponse({"reply": "Please type something."})

        # Step 1: Ask Gemini to create SQL
        prompt = f"""
        You are an expert SQL assistant.
        Generate a single SQL query for SQLite database that answers the question: "{user_message}".
        Do not include explanations or markdown formatting.
        """
        gemini_response = model.generate_content(prompt)
        sql_query = gemini_response.text.strip()

        # Remove markdown fences like ```sql
        sql_query = re.sub(r"```(?:sql|sqlite)?", "", sql_query, flags=re.IGNORECASE).strip("` \n")

        # Step 2: Run SQL query
        db_reply = ""
        try:
            conn = sqlite3.connect("classicmodels.db")
            cursor = conn.cursor()
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            db_reply = str(rows) if rows else "No results found."
            conn.close()
        except Exception as e:
            db_reply = f"SQL error: {e}"

        # Step 3: Final answer from Gemini using SQL result
        final_prompt = f"User asked: {user_message}\nSQL result: {db_reply}\nAnswer in plain language."
        final_answer = model.generate_content(final_prompt).text.strip()

        return JSONResponse({"reply": final_answer})

    except Exception as e:
        return JSONResponse({"reply": f"Sorry, something went wrong: {e}"})

# ==== Run App ====
if __name__ == "__main__":
    import uvicorn
    print(f"===== Application Startup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    uvicorn.run(app, host="0.0.0.0", port=7860)
