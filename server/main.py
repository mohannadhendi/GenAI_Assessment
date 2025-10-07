from fastapi import FastAPI ,Depends
from server.db import Base, engine, SessionLocal
from server.models import *
from server.routes.base import router as base_router
from server.routes.chat import router as chat_router


app = FastAPI()

@app.on_event("startup")
def startup_db_client():
    try:
        print("Loaded tables:", Base.metadata.tables.keys())

        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("Connected to the PostgreSQL database!")
    except Exception as e:
        print(f"Failed to connect to PostgreSQL: {e}")

# Shutdown: close sessions if necessary
@app.on_event("shutdown")
def shutdown_db_client():
    SessionLocal.close_all()
    print("Database connection closed.")


app.include_router(base_router)
app.include_router(chat_router)

