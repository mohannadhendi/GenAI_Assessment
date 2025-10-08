from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Type
import json, re
from server.db import SessionLocal
from server.models import Book


class UpdatePriceInput(BaseModel):
    """Accepts flexible payloads (handles either price or qty keys)."""
    isbn: Any = Field(..., description="Book ISBN (string or embedded JSON)")
    price: Any = Field(None, description="New price (float, or may arrive as 'qty')")


class UpdatePriceTool(BaseTool):
    name: str = "update_price"
    description: str = "Update the price of a book in the inventory."
    args_schema: Type[BaseModel] = UpdatePriceInput

    def _run(self, isbn: Any, price: Any = None):
        db = SessionLocal()
        try:
            # Handle entire input embedded as JSON string
            if isinstance(isbn, str) and price is None:
                try:
                    cleaned = re.sub(r"([{,]\s*)(\w+)\s*:", r'\1"\2":', isbn.replace("'", '"'))
                    parsed = json.loads(cleaned)
                    isbn = parsed.get("isbn")
                    price = parsed.get("price") or parsed.get("qty")
                except Exception:
                    pass

            # If price still missing, default to 0 or error
            if price is None:
                return {"error": "Missing 'price' or 'qty' field."}

            # Ensure correct types
            try:
                price = float(price)
            except Exception:
                return {"error": f"Invalid price format: {price}"}

            if not isinstance(isbn, str):
                return {"error": f"Invalid ISBN format: {isbn}"}

            # Update DB record
            book = db.query(Book).filter_by(isbn=isbn).first()
            if not book:
                return {"error": f"Book with ISBN {isbn} not found."}

            book.price = price
            db.commit()

            return {"isbn": isbn, "updated_price": price}

        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented.")
