import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import os

# Gemini API key
os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "classicmodels.db"

# Run SQL
def query_database(sql_query):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return f"[DB ERROR] {e}"

# Talk to Gemini
def ask_gemini(user_message):
    try:
        model = genai.GenerativeModel("gemini-pro")

        # Step 1: Get SQL from Gemini
        sql_prompt = f"""
        The database is classicmodels.db with tables:
        customers, orders, orderdetails, products, employees, offices, payments, productlines.
        User: "{user_message}"
        Write only a valid SQLite SELECT query to answer.
        """
        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()

        # Cleanup markdown fences
        if sql_query.startswith("```"):
            parts = sql_query.split("```")
            if len(parts) >= 2:
                sql_query = parts[1]
        sql_query = sql_query.replace("sqlite", "", 1).strip()

        print(f"[User]: {user_message}")
        print(f"[Gemini SQL Cleaned]: {sql_query}")

        # Step 2: Execute SQL
        db_result = query_database(sql_query)

        # Step 3: Summarize answer
        answer_prompt = f"""
        The user asked: {user_message}
        The SQL query run was: {sql_query}
        The database returned: {db_result}
        Please summarize the answer in plain English.
        """
        answer_response = model.generate_content(answer_prompt)

        # Prevent empty responses
        answer_text = answer_response.text.strip() if answer_response and answer_response.text else "I couldn't find an answer."

        return {
            "sql": sql_query,
            "db_result": db_result,
            "answer": answer_text
        }

    except Exception as e:
        return {"error": str(e), "answer": "An error occurred while processing your request."}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "chat_history": []})

@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, user_input: str = Form(...)):
    result = ask_gemini(user_input)
    chat_history = [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": result.get("answer", "Error occurred.")}
    ]
    return templates.TemplateResponse("index.html", {"request": request, "chat_history": chat_history})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
