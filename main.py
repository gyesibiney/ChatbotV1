from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import google.generativeai as genai
import os

app = FastAPI()

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# DB connection
DB_PATH = "classicmodels.db"

def run_query(query):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(user_input: str = Form(...)):
    print(f"[USER INPUT] {user_input}")

    try:
        # Ask Gemini to create a SQL query
        prompt = f"You are a SQL expert. Create an SQL query for SQLite to answer: '{user_input}' using the classicmodels database schema."
        gemini_response = model.generate_content(prompt)
        sql_query = gemini_response.text.strip()

        print(f"[GEMINI SQL] {sql_query}")

        # Run query
        results = run_query(sql_query)
        if results is None:
            return {"response": "I had trouble running that query."}

        # Build answer
        if len(results) == 0:
            answer = "No matching records found."
        else:
            answer = f"I found {len(results)} record(s): {results}"

        return {"response": answer}

    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        return {"response": "Sorry, something went wrong while processing your question."}
