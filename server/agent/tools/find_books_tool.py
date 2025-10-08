from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from sqlalchemy import or_, func
from server.db import SessionLocal
from server.models import Book
import json
import unicodedata
import re


class FindBooksInput(BaseModel):
    q: str = Field(..., description="Search text for book title or author")
    by: str = Field("title", description="Field to search: 'title' or 'author'")


class FindBooksTool(BaseTool):
    name: str = "find_books"
    description: str = "Find books by title or author. Args: { q, by }"
    args_schema: type[BaseModel] = FindBooksInput

    def normalize_text(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFKD", text)
        text = text.replace("’", "'").replace("“", '"').replace("”", '"')
        return text.strip().lower()

    def safe_parse(self, data):
        """Parse input robustly whether it's dict, JSON, or pseudo-JSON."""
        if isinstance(data, dict):
            return data
        if isinstance(data, FindBooksInput):
            return data.dict()

        # Try real JSON first
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                # Handle pseudo-JSON like { q: "abc", by: "title" }
                cleaned = re.sub(r"([a-zA-Z_]+)\s*:", r'"\1":', data)
                cleaned = cleaned.replace("'", '"')
                try:
                    return json.loads(cleaned)
                except Exception:
                    return {"q": data, "by": "title"}

        return {"q": str(data), "by": "title"}

    def _run(self, data):
        parsed = self.safe_parse(data)
        q = self.normalize_text(parsed.get("q", ""))
        by = parsed.get("by", "title").lower()

        db = SessionLocal()
        try:
            query = db.query(Book)

            if by == "author":
                results = query.filter(func.lower(Book.author).ilike(f"%{q}%")).all()
            elif by == "title":
                results = query.filter(func.lower(Book.title).ilike(f"%{q}%")).all()
            else:
                results = query.filter(
                    or_(
                        func.lower(Book.title).ilike(f"%{q}%"),
                        func.lower(Book.author).ilike(f"%{q}%"),
                    )
                ).all()

            print(f"[DEBUG] Searching for '{q}' by '{by}' → {len(results)} results")

            return [
                {
                    "isbn": b.isbn,
                    "title": b.title,
                    "author": b.author,
                    "price": b.price,
                    "stock": b.stock,
                }
                for b in results
            ]
        finally:
            db.close()
