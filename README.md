# Gemini SQL Chatbot - Classic Models

This project is a **FastAPI-powered chatbot** that uses **Google's Gemini model** to translate natural language questions into SQL queries against the **Classic Models** sample database.  

The chatbot provides a simple web interface where users can ask questions (e.g., *“Show all customers from Germany”*) and get results from the SQLite database in plain English.

---

## 🚀 Features
- Natural language → SQL query generation using **Gemini API**
- Works with the **Classic Models** SQLite database
- Lightweight **FastAPI backend**
- Minimal **HTML/JS frontend** with interactive chat
- Example queries to guide users

---

## 📂 Project Structure


DB_NAME = "classicmodels.db"  # Automatically persists between deploys

'''

📦 Files Included
/Repository
├── app.py               
├── classicmodels.db     
├── requirements.txt  
├── templates/
│   └── index.html
└── static/
    └── style.css
└── README.md            

🌟 Example Queries
-- These get translated from natural language:
"Show all customers from Germany"
"List all Ford products"
"Find all orders placed in 2005"
"Show total sales by each country"
"List all product lines and their descriptions"
   
'''

2. Install Dependencies
   pip install fastapi uvicorn google-generativeai fastapi uvicorn mysql-connector-python google-generativeai python-multipart jinja2

3. Setup Environment Variables
Set your Gemini API Key:

export GEMINI_API_KEY="your_api_key_here"



⚠️ Notes
Make sure your classicmodels.db schema matches the expected tables:

customers

employees

offices

orders

orderdetails

payments

products

productlines

The Gemini model sometimes generates invalid SQL — errors are caught and displayed in chat.




























---
title: ChatBotV1
emoji: ⚡
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
