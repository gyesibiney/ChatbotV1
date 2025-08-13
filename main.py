from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import os

app = FastAPI()

# Static + templates setup
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# DB Path
DB_PATH = os.getenv("DB_PATH", "classicmodels.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(message: str = Form(...)):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT productName, productLine, buyPrice FROM products WHERE productName LIKE ? LIMIT 5",
            (f"%{message}%",)
        )
        products = cursor.fetchall()

        if not products:
            response = "Sorry, I couldn't find any matching products."
        else:
            response = "Here’s what I found:<br>"
            for p in products:
                response += f"- {p['productName']} ({p['productLine']}) — ${p['buyPrice']}<br>"

        conn.close()
        return JSONResponse({"reply": response})

    except Exception as e:
        return JSONResponse({"reply": f"Error: {str(e)}"})
