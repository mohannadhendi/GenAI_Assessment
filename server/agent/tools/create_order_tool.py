from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Type
import json, re
from server.db import SessionLocal
from server.models import Book, Order, OrderItem


# Loosen the validation schema
class CreateOrderInput(BaseModel):
    """Accept any raw payload from the LLM without validation errors."""
    customer_id: Any = Field(..., description="Customer ID (int or embedded JSON string)")
    items: Any = Field(None, description="List of ordered items or embedded JSON string")


class CreateOrderTool(BaseTool):
    name: str = "create_order"
    description: str = "Create a new order and update book stock."
    args_schema: Type[BaseModel] = CreateOrderInput

    def _run(self, customer_id: Any, items: Any = None):
        db = SessionLocal()
        try:
            if isinstance(customer_id, str) and items is None:
                raw = customer_id.strip()
                try:
                    clean = re.sub(r"([{,]\s*)(\w+)\s*:", r'\1"\2":', raw.replace("'", '"'))
                    parsed = json.loads(clean)
                    customer_id = int(parsed.get("customer_id"))
                    items = parsed.get("items", [])
                except Exception as e:
                    return {"error": f"Failed to parse tool input: {e}"}

            if isinstance(items, str):
                try:
                    items = json.loads(items.replace("'", '"'))
                except Exception as e:
                    return {"error": f"Invalid 'items' format: {e}"}

            try:
                customer_id = int(customer_id)
            except Exception:
                pass

            if not isinstance(items, list):
                return {"error": f"Expected a list for 'items', got {type(items)}"}

            # --- Create order ---
            order = Order(customer_id=customer_id, created_at=datetime.utcnow())
            db.add(order)
            db.flush()
            processed, warnings = [], []

            for item in items:
                print(f"🔹 [DEBUG] Processing item: {item}")
                isbn = item.get("isbn")
                qty = int(item.get("qty", 0))

                book = db.query(Book).filter_by(isbn=isbn).first()
                if not book:
                    warnings.append(f"Book '{isbn}' not found — skipped.")
                    continue
                if book.stock < qty:
                    warnings.append(f"Not enough stock for '{book.title}'.")
                    continue

                db.add(OrderItem(order_id=order.id, isbn=isbn, qty=qty))
                book.stock -= qty
                processed.append({
                    "title": book.title,
                    "isbn": book.isbn,
                    "ordered_qty": qty,
                    "remaining_stock": book.stock
                })
            db.commit()
            return {"order_id": order.id, "items": processed, "warnings": warnings}

        except Exception as e:
            db.rollback()
            return {"error": str(e)}
        finally:
            db.close()

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented.")
