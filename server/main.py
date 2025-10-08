import os
import threading
import time
import subprocess
from fastapi import FastAPI, Depends
from server.db import Base, engine, SessionLocal
from server.models import *
from server.routes.base import router as base_router
from server.routes.chat import router as chat_router
from server.routes.session_routes import router as session_router 
from server.routes.message_routes import router as message_router




app = FastAPI(title="Library Desk Agent API")

@app.on_event("startup")
def startup_db_client():
    try:
        print("Loaded tables:", Base.metadata.tables.keys())
        Base.metadata.create_all(bind=engine)
        print("Connected to the PostgreSQL database!")
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")

@app.on_event("shutdown")
def shutdown_db_client():
    SessionLocal.close_all()
    print("Database connection closed.")

# Register routes
app.include_router(base_router)
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(message_router)





def launch_streamlit():
    """Runs Streamlit in a separate thread."""
    time.sleep(3)  # allow FastAPI to boot first
    cmd = [
        "streamlit", "run", "app/chat_ui.py",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false"
    ]
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    subprocess.run(cmd, env=env)



if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Library Desk Agent...")

    # Start Streamlit background thread
    streamlit_thread = threading.Thread(target=launch_streamlit, daemon=True)
    streamlit_thread.start()

    print("⚙️ FastAPI starting on http://127.0.0.1:5000 ...")
    uvicorn.run("server.main:app", host="127.0.0.1", port=5000, reload=True)