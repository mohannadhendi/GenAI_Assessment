from fastapi import FastAPI ,Depends
from server.config import get_settings , Settings
from server.db import Base, engine, SessionLocal
from server.models import *


settings = get_settings()

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
    print("🔌 Database connection closed.")



@app.get("/")
def root(app_settings:Settings = Depends(get_settings)):
        app_name = app_settings.APP_NAME
        app_version = app_settings.APP_VERSION

        return {
            "app_name": app_name, 
            "app_version": app_version
            }   

