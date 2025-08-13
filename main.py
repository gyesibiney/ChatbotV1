import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import os
import traceback

DB_PATH = "classicmodels.db"

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ ERROR: GEMINI_API_KEY is not set!")
else:
    genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def query_database(sql_query):
    """Run SQL and return results as list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def ask_gemini(user_message):
    try:
        print(f"\n[User]: {user_message}")

        # 1️⃣ Ask Gemini for SQL
        sql_prompt = f"""
The database is classicmodels.db with tables:
customers, orders, orderdetails, products, employees, offices, payments, productlines.
User: "{user_message}"
Write only a valid SQLite SELECT query to answer.
"""
        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()
        print(f"[Gemini SQL]: {sql_query}")

        # 2️⃣ Run SQL
        try:
            db_results = query_database(sql_query)
            print(f"[DB Results]: {db_results}")
        except Exception as e:
            print("[DB ERROR]", e)
            db_results = []
            sql_query = f"ERROR running SQL: {e}"

        # 3️⃣ Final conversational answer
        final_prompt = f"""
User: {user_message}
SQL Used: {sql_query}
Results: {db_results}
Answer conversationally.
"""
        final_response = model.generate_content(final_prompt)
        print(f"[Gemini Answer]: {final_response.text.strip()}")
        return final_response.text.strip()

    except Exception as e:
        print("❌ ERROR in ask_gemini:", traceback.format_exc())
        return f"Sorry, an error occurred: {e}"


@app.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "chat_history": []})


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    reply = ask_gemini(message)
    chat_history = [
        {"sender": "You", "text": message},
        {"sender": "Bot", "text": reply}
    ]
    return templates.TemplateResponse("index.html", {"request": request, "chat_history": chat_history})
