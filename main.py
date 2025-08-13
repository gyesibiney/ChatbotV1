import sqlite3
import re
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai
import os

# ========= CONFIG =========
DB_PATH = "classicmodels.db"
GEMINI_MODEL = "gemini-1.5-flash"   # you can change to your specific Gemini model
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# ========= APP =========
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ========= HELPERS =========

def clean_sql_query(sql_code: str) -> str:
    """
    Remove markdown code fences (```sql, ```sqlite, ```).
    Also trims whitespace.
    """
    # Remove triple backticks with language
    sql_code = re.sub(r"```(?:sql|sqlite)?", "", sql_code, flags=re.IGNORECASE)
    # Remove ending triple backticks
    sql_code = sql_code.replace("```", "")
    return sql_code.strip()

def run_sql_query(query: str):
    """
    Run the SQL query on the database and return rows.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        conn.close()
        return {"columns": col_names, "rows": rows}
    except Exception as e:
        return {"error": str(e)}

def gemini_generate(prompt: str):
    """
    Send prompt to Gemini and return text.
    """
    model = genai.GenerativeModel(GEMINI_MODEL)
    chat = model.start_chat(history=[])
    response = chat.send_message(prompt)
    return response.text

# ========= API =========
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(chat_req: ChatRequest):
    user_message = chat_req.message.strip()

    # Step 1: Ask Gemini to determine SQL or answer
    prompt = f"""
You are a chatbot connected to a SQLite database of the classicmodels company.
If the user asks something that requires database lookup, output only the SQL query.
Otherwise, answer normally.

Database schema:
Tables: products, customers, employees, orders, orderdetails, payments, offices, productlines

User: {user_message}
    """
    gemini_response = gemini_generate(prompt)

    # Step 2: If Gemini returns SQL, execute it
    if "SELECT" in gemini_response.upper():
        sql_query = clean_sql_query(gemini_response)
        db_result = run_sql_query(sql_query)
        if "error" in db_result:
            return {"bot": f"[DB ERROR] {db_result['error']}"}
        return {
            "bot": f"Query successful. Result: {json.dumps(db_result, indent=2)}",
            "sql": sql_query
        }
    else:
        return {"bot": gemini_response}

# ========= UI =========
@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    with open("static/index.html") as f:
        return HTMLResponse(f.read())
