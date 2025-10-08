from langchain.tools import BaseTool
from pydantic import BaseModel, Field, ValidationError
from server.db import SessionLocal
from server.models import Book
import json, re


class RestockBookTool(BaseTool):
    name: str = "restock_book"
    description: str = "Increase the stock quantity for a book. Args: { isbn, qty }"

    def safe_parse(self, data):
        """Robustly parse LangChain input (dict, JSON, pseudo-JSON, or nested malformed dict)."""
        if isinstance(data, dict):
            # Case: nested malformed JSON inside isbn
            if isinstance(data.get("isbn"), str) and "{ isbn" in data["isbn"]:
                raw = data["isbn"]
                cleaned = re.sub(r"([a-zA-Z_]+)\s*:", r'"\1":', raw)
                cleaned = cleaned.replace("'", '"')
                try:
                    return json.loads(cleaned)
                except Exception:
                    pass
            return data

        if isinstance(data, str):
            # Try clean JSON
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                # Fix pseudo-JSON format like { isbn: '...', qty: 10 }
                cleaned = re.sub(r"([a-zA-Z_]+)\s*:", r'"\1":', data)
                cleaned = cleaned.replace("'", '"')
                try:
                    return json.loads(cleaned)
                except Exception:
                    return {"isbn": data, "qty": 1}

        return {"isbn": str(data), "qty": 1}

    def _run(self, data):
        """Safely restock a book by ISBN."""
        parsed = self.safe_parse(data)
        isbn = parsed.get("isbn")
        qty = parsed.get("qty")

        # Fallback: if qty still missing, try to extract from raw text
        if qty is None:
            match = re.search(r"qty[^0-9]*([0-9]+)", str(data))
            if match:
                qty = int(match.group(1))
            else:
                qty = 1

        print(f"[DEBUG] Parsed restock input → {parsed}")

        db = SessionLocal()
        try:
            book = db.query(Book).filter_by(isbn=isbn).first()
            if not book:
                return {"error": f"Book with ISBN {isbn} not found."}

            book.stock += int(qty)
            db.commit()
            return {"isbn": isbn, "new_stock": book.stock}
        finally:
            db.close()
