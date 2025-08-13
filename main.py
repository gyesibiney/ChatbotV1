import sqlite3
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import os

# 1️⃣ Gemini API Key
os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# 2️⃣ FastAPI app
app = FastAPI()

# Static files & templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

DB_PATH = "classicmodels.db"

# 3️⃣ Database query function
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

# 4️⃣ Ask Gemini (SQL + answer)
def ask_gemini(user_message):
    try:
        # --- Ask Gemini for SQL ---
        sql_prompt = f"""
        The database is classicmodels.db with tables:
        customers, orders, orderdetails, products, employees, offices, payments, productlines.
        User: "{user_message}"
        Write only a valid SQLite SELECT query to answer.
        """
        model = genai.GenerativeModel("gemini-pro")
        sql_response = model.generate_content(sql_prompt)
        sql_query = sql_response.text.strip()

        # 🛠 Remove markdown fences if present
        if sql_query.startswith("```"):
            parts = sql_query.split("```")
            if len(parts) >= 2:
                sql_query = parts[1]
        sql_query = sql_query.replace("sqlite", "", 1).strip()

        print(f"[User]: {user_message}")
        print(f"[Gemini SQL Cleaned]: {sql_query}")

        # --- Execute SQL ---
        db_result = query_database(sql_query)

        # --- Ask Gemini to summarize ---
        answer_prompt = f"""
        The user asked: {user_message}
        The SQL query run was: {sql_query}
        The database returned: {db_result}
        Please summarize the answer in plain English.
        """
        answer_response = model.generate_content(answer_prompt)

        return {
            "sql": sql_query,
            "db_result": db_result,
            "answer": answer_response.text.strip()
        }

    except Exception as e:
        return {"error": str(e)}

# 5️⃣ Web routes
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

# 6️⃣ Run locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
