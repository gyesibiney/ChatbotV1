from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import mysql.connector
import google.generativeai as genai

# -----------------------
# App setup
# -----------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -----------------------
# Config
# -----------------------
API_KEY = os.getenv("API_KEY")  # Optional for API security
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "classicmodels")

# Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Please set GEMINI_API_KEY in your environment")

genai.configure(api_key=GEMINI_API_KEY)
llm_model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------
# Example questions
# -----------------------
EXAMPLE_QUESTIONS = [
    "List the top 5 customers by total payments",
    "Show the total sales by product line",
    "Which employees report to Mary Patterson?",
]

# -----------------------
# Chat memory
# -----------------------
chat_history = []

# -----------------------
# DB connection helper
# -----------------------
def run_sql_query(sql):
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return rows

# -----------------------
# Process query with Gemini
# -----------------------
def process_query(user_input):
    prompt = f"""
You are a helpful assistant for the ClassicModels MySQL database.

Schema:
- Customers(customerNumber, customerName, contactLastName, contactFirstName, phone, addressLine1, addressLine2, city, state, postalCode, country, salesRepEmployeeNumber, creditLimit)
- Orders(orderNumber, orderDate, requiredDate, shippedDate, status, comments, customerNumber)
- OrderDetails(orderNumber, productCode, quantityOrdered, priceEach, orderLineNumber)
- Products(productCode, productName, productLine, productScale, productVendor, productDescription, quantityInStock, buyPrice, MSRP)
- Employees(employeeNumber, lastName, firstName, extension, email, officeCode, reportsTo, jobTitle)
- Offices(officeCode, city, phone, addressLine1, addressLine2, state, country, postalCode, territory)
- Payments(customerNumber, checkNumber, paymentDate, amount)
- ProductLines(productLine, textDescription, htmlDescription, image)

User asked: {user_input}

Return only the SQL query without explanation.
"""
    response = llm_model.generate_content(prompt)
    sql_query = response.text.strip().strip("`")
    try:
        rows = run_sql_query(sql_query)
    except Exception as e:
        return f"Error executing query: {e}"
    return f"SQL: {sql_query}\n\nResults: {rows}"

# -----------------------
# Routes
# -----------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "api_key_required": bool(API_KEY),
        "example_questions": EXAMPLE_QUESTIONS,
        "chat_history": chat_history
    })

@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    if len(message) > 2000:
        raise HTTPException(status_code=413, detail="Message too long")

    chat_history.append(("user", message))
    try:
        answer = process_query(message)
    except Exception as e:
        answer = f"Error: {str(e)}"

    chat_history.append(("assistant", answer))
    return templates.TemplateResponse("index.html", {
        "request": request,
        "api_key_required": bool(API_KEY),
        "example_questions": EXAMPLE_QUESTIONS,
        "chat_history": chat_history
    })

@app.post("/query")
async def query_api(message: str = Form(...), api_key: str = Form(None)):
    if API_KEY and api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return {"response": process_query(message)}
