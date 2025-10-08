# 📚 Library Desk Agent

An **AI-powered Library Management Assistant** built with **FastAPI**, **LangChain**, and **Streamlit**.  
It helps manage books, customers, and orders through natural language queries.

## 🚀 Features

- 🤖 GPT-powered intelligent assistant (LangChain Agent)
- ⚡ FastAPI backend with tool orchestration
- 🖥️ Streamlit interactive frontend
- 🗄️ PostgreSQL database with SQLAlchemy ORM
- 🔄 Auto tool chaining (find_books → restock_book → create_order → ...)
- 💬 Persistent chat sessions with database logging

## 🧩 Project Structure

```
GenAI_Assessment/
├── app/
│   └── chat_ui.py             # Streamlit frontend
├── server/
│   ├── main.py                # FastAPI + Streamlit launcher
│   ├── db.py                  # Database connection
│   ├── models/                # SQLAlchemy models
│   ├── agent/
│   │   ├── chains/            # LangChain agent logic
│   │   └── tools/             # Custom AI tools
│   ├── routes/                # FastAPI endpoints
│   └── config.py              # Environment settings
├── db/
│   └── seed.py                # Seed script to populate sample data
└── README.md
```

## ⚙️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd GenAI_Assessment
```

### 2. Create and Activate Virtual Environment

```bash
conda create -n desk-agent python=3.11 -y
conda activate desk-agent
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```env
APP_NAME="" 
APP_VERSION=""
OPENAI_API_KEY=""
POSTGRES_DB_URL=""
POSTGRES_DB_NAME=""
POSTGRES_DB_USER=""
POSTGRES_DB_PASSWORD=""
API_URL=""
```

**Environment Variables:**
- `APP_NAME`: Application name displayed in the UI
- `APP_VERSION`: Current version of the application
- `OPENAI_API_KEY`: Your OpenAI API key for GPT integration
- `POSTGRES_DB_URL`: Full PostgreSQL connection string
- `POSTGRES_DB_NAME`: Database name (e.g., `library_db`)
- `POSTGRES_DB_USER`: Database username
- `POSTGRES_DB_PASSWORD`: Database password
- `API_URL`: Backend API endpoint for chat requests

## 🌱 Database Setup

### Automatic Table Creation
When you run the application for the first time, all database tables are created automatically through SQLAlchemy ORM migrations.

### Data Seeding
To populate initial books, customers, and sample data:

```bash
cd ~/path/to/your/project
python -m db.seed
```


### Manual Schema Setup (Troubleshooting)
If you encounter any database issues, you can manually create the schema using the provided SQL file:

```bash
psql -U your_username -d library_db -f seed.sql
```

This will create all necessary tables and constraints for the application.

## ▶️ Run the Project

You can run FastAPI and Streamlit together from one terminal:

```bash
python -m server.main
```

Once launched:
- FastAPI runs on → `http://127.0.0.1:5000`
- Streamlit UI runs on → `http://127.0.0.1:8501`

## 🧠 Example Queries (Test Cases)

You can test directly in the Streamlit chat or via API calls.

### 🔍 Find Book
```json
{ "query": "Find books by Robert C. Martin" }
```

### 📦 Restock Book
```json
{ "query": "Restock Clean Code book by 45" }
```

### 🛒 Create Order
```json
{ "query": "Create an order for customer 2 for 2 copies of Clean Code" }
```

### 💰 Update Price
```json
{ "query": "Update the price of Clean Code to 50 dollars" }
```

### 📑 Order Status
```json
{ "query": "What is the status of order 2?" }
```

### 📉 Inventory Summary
```json
{ "query": "Show me all books that are running low on stock" }
```

## 🧪 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health Check |
| `/chat` | POST | Send a query to the AI agent |
| `/sessions` | GET | List all chat sessions |
| `/messages/{session_id}` | GET | Retrieve chat history for a specific session |


## 👨‍💻 Developed By:

**Mohannad Hendi**  
Senior AI Engineer • Automation Specialist • Data Scientist
