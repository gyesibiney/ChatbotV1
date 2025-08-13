from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# === Configure Gemini API ===
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# === Setup FastAPI ===
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_PATH = "classicmodels.db"

# ==== UI with examples ====
@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gemini SQL Chatbot</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; }
            .examples button {
                margin: 3px;
                padding: 5px 10px;
                background: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                cursor: pointer;
            }
            .examples button:hover {
                background: #ddd;
            }
            #chat-box { border:1px solid #ccc; padding:10px; height:300px; overflow-y:auto; margin-top:15px; }
            #user-input { width:80%; padding: 5px; }
            button { padding: 5px 10px; }
        </style>
    </head>
    <body>
        <h1>Chat with Classic Models Database</h1>
        <p>
            This chatbot is connected to <b>classicmodels.db</b>, a sample business database 
            containing data about cars, customers, employees, offices, orders, and payments. 
            You can ask questions in plain English, and it will fetch real data from the database.
        </p>

        <h3>Example Questions:</h3>
        <div class="examples">
            <button onclick="sendExample('Show all Ford cars available')">Show all Ford cars available</button>
            <button onclick="sendExample('List all employees and their job titles')">List all employees and their job titles</button>
            <button onclick="sendExample('How many customers are in the USA?')">How many customers are in the USA?</button>
            <button onclick="sendExample('List all orders placed in 2004')">List all orders placed in 2004</button>
            <button onclick="sendExample('Show the total payments received from each customer')">Show the total payments received from each customer</button>
        </div>

        <div id="chat-box"></div>
        <input id="user-input" type="text" placeholder="Type a message...">
        <button onclick="sendMessage()">Send</button>

        <script>
        async function sendExample(text) {
            document.getElementById("user-input").value = text;
            await sendMessage();
        }

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

# ==== Chat endpoint ====
@app.post("/chat")
async def chat_with_db(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message", "")

        # Ask Gemini to create an SQL query for the database
        prompt = f"""
        You are a SQL assistant. The database schema is from classicmodels.db.
        Tables include: customers, employees, offices, orders, orderdetails, payments, products, productlines.
        User question: {user_message}
        Return ONLY the SQL query without explanations.
        """
        gemini_response = model.generate_content(prompt)
        sql_query = gemini_response.text.strip()

        # Run the generated SQL
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        results = cursor.fetchall()
        conn.close()

        return JSONResponse({"reply": str(results)})

    except Exception as e:
        return JSONResponse({"reply": f"Error: {str(e)}"})

