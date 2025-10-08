from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Type
import json, re
from server.db import SessionLocal
from server.models import Book


class InventorySummaryInput(BaseModel):
    """Accepts flexible input for stock threshold (optional)."""
    threshold: Any = Field(
        5,
        description="Optional stock threshold (int). Defaults to 5 if not provided."
    )


class InventorySummaryTool(BaseTool):
    name: str = "inventory_summary"
    description: str = "List all books that are low in stock."
    args_schema: Type[BaseModel] = InventorySummaryInput

    def _run(self, threshold: Any = 5):
        db = SessionLocal()
        try:
            # --- Normalize the threshold argument ---
            if isinstance(threshold, str):
                try:
                    cleaned = re.sub(r"([{,]\s*)(\w+)\s*:", r'\1"\2":', threshold.replace("'", '"'))
                    parsed = json.loads(cleaned)
                    threshold = parsed.get("threshold", threshold)
                except Exception:
                    pass

            try:
                threshold = int(threshold)
            except Exception:
                threshold = 5  # fallback to default

            # --- Query books ---
            books = db.query(Book).filter(Book.stock <= threshold).all()

            if not books:
                return {"message": f"No books found below stock threshold ({threshold})."}

            return {
                "threshold": threshold,
                "low_stock_books": [
                    {"title": b.title, "isbn": b.isbn, "stock": b.stock}
                    for b in books
                ]
            }

        except Exception as e:
            db.rollback()
            return {"error": str(e)}

        finally:
            db.close()

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented.")
