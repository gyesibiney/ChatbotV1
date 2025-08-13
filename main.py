import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import os

# ----------------------
# CONFIGURATION
# ----------------------
DB_PATH = "classicmodels.db"

# Set your Gemini API key (must be in Hugging Face Secrets or .env)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

# ----------------------
# FASTAPI SETUP
# ----------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def query_database(sql_query):
    """Execute a SQL query and return results as list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def ask_gemini(user_message):
    """
    Generate SQL query, fetch results from DB,
    and pass both question + results to Gemini for reasoning.
    """
    # Step 1: Ask Gemini to create an SQL query for SQLite
    sql_prompt = f"""
You are a data assistant. The database schema is from 'classicmodels.db' which contains tables like:
- customers
- orders
- orderdetails
- products
- employees
- offices
- payments
- productlines

The user asked: "{user_message}"

Write ONLY a valid SQL SELECT statement for SQLite to answer this question.
Do not use code fences, explanations, or any text other than the SQL query.
    """
    sql_response = model.generate_content(sql_prompt)
    sql_query = sql_response.text.strip()

    # Step 2: Run SQL on our local database
    try:
        db_results = query_database(sql_query)
    except Exception as e:
        db_results = []
        sql_query = f"ERROR: {e}"

    # Step 3: Ask Gemini to answer conversationally using the DB results
    final_prompt = f"""
You are a friendly sales assistant for a car/motorcycle/vehicle parts store.
User question: {user_message}
SQL Query Used: {sql_query}
Database Results: {db_results}

Please answer in natural language, summarizing the information for the user.
If no results, politely say we don't have that item.
    """
    final_response = model.generate_content(final_prompt)
    return final_response.text.strip()


@app.get("/", response_class=HTMLResponse)
async def get_chat(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "chat_history": []})


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    reply = ask_gemini(message)

    # Keep chat history in session (for simplicity here, just return last exchange)
    chat_history = [
        {"sender": "You", "text": message},
        {"sender": "Bot", "text": reply}
    ]
    return templates.TemplateResponse("index.html", {"request": request, "chat_history": chat_history})
