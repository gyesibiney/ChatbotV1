# 🤖 Gemini SQL ChatBot – Classic Models Database

[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20HuggingFace-Spaces-blue)](https://huggingface.co/spaces/gyesibiney/ChatBotV1)

An interactive **FastAPI-powered chatbot** that connects **Google Gemini** with the **Classic Models database (SQLite)**.  
Users can ask natural language questions, and the bot will:

1. Convert the question into a valid **SQL query** (via Gemini).
2. Execute the query on the `classicmodels.db` database.
3. Return the results in **plain English**.

Deployed on **Hugging Face Spaces** 🚀:  
👉 [Live Demo](https://huggingface.co/spaces/gyesibiney/ChatBotV1)

---

## ✨ Features

- 🔍 Ask natural language questions about customers, employees, products, orders, and payments.  
- 🧠 Uses **Google Gemini (gemini-1.5-flash)** for SQL query generation and result summarization.  
- 🗄️ Backed by the **Classic Models database** in SQLite.  
- 🌐 Simple **FastAPI UI** with interactive chat.  
- 📊 Pre-loaded example questions (e.g., *"Show all customers from Germany"*).  

---

## 🛠️ Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) – Backend & REST API  
- [SQLite](https://www.sqlite.org/) – Classic Models database  
- [Google Gemini API](https://ai.google.dev/) – Natural Language to SQL + Answer generation  
- [Hugging Face Spaces](https://huggingface.co/spaces) – Deployment  

---

## 🚀 Getting Started (Local Development)

### 1. Clone the repo
```bash
git clone https://huggingface.co/spaces/gyesibiney/ChatBotV1
cd ChatBotV1

2. Create virtual environment & install dependencies
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt

3. Set up environment variable
Add your Gemini API key to .env:
GEMINI_API_KEY=your_api_key_here

4. Run the app
uvicorn app:app --host 0.0.0.0 --port 7860 --reload

📂 Repository Structure
ChatBotV1/
│── app.py              # FastAPI main app
│── classicmodels.db    # SQLite database
│── static/             # CSS/JS for UI
│── requirements.txt    # Dependencies
│── README.md           # Project docs





---
title: ChatBotV1
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
