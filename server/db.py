from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from server.config import get_settings

settings = get_settings()

# Build database URL
DATABASE_URL = (
    f"postgresql+psycopg2://{settings.POSTGRES_DB_USER}:{settings.POSTGRES_DB_PASSWORD}"
    f"@{settings.POSTGRES_DB_URL}/{settings.POSTGRES_DB_NAME}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
