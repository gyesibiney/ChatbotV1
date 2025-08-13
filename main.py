from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import time

# Prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI()

# Serve static files (optional: for CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

DB_PATH = "classicmodels.db"

# ----- Prometheus Metrics -----
REQUEST_COUNT = Counter(
    "saleschat_requests_total",
    "Total number of requests to the Sales Chatbot",
    ["method", "endpoint"]
)
CHAT_MESSAGES = Counter(
    "saleschat_chat_messages_total",
    "Total number of chat messages processed"
)
REQUEST_LATENCY = Histogram(
    "saleschat_request_latency_seconds",
    "Latency of requests in seconds",
    ["endpoint"]
)


def query_database(question: str):
    """Basic DB query simulation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    answer = ""

    if "customers" in question.lower():
        cursor.execute("SELECT customerName, country FROM customers LIMIT 5;")
        rows = cursor.fetchall()
        answer = "\n".join([f"{name} ({country})" for name, country in rows])

    elif "products" in question.lower():
        cursor.execute("SELECT productName, buyPrice FROM products LIMIT 5;")
        rows = cursor.fetchall()
        answer = "\n".join([f"{name} - ${price}" for name, price in rows])

    else:
        answer = "Sorry, I can't answer that yet. Try asking about 'customers' or 'products'."

    conn.close()
    return answer


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    REQUEST_COUNT.labels(method="GET", endpoint="/").inc()
    start_time = time.time()

    response = templates.TemplateResponse("index.html", {"request": request, "chat_history": []})

    REQUEST_LATENCY.labels(endpoint="/").observe(time.time() - start_time)
    return response


@app.post("/chat", response_class=HTMLResponse)
async def chat(request: Request, message: str = Form(...)):
    REQUEST_COUNT.labels(method="POST", endpoint="/chat").inc()
    CHAT_MESSAGES.inc()
    start_time = time.time()

    answer = query_database(message)
    response = templates.TemplateResponse(
        "index.html",
        {"request": request, "chat_history": [(message, answer)]}
    )

    REQUEST_LATENCY.labels(endpoint="/chat").observe(time.time() - start_time)
    return response


@app.get("/metrics")
async def metrics():
    """Prometheus scraping endpoint."""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
