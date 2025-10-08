from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Type
import json, re
from server.db import SessionLocal
from server.models import Book, Order, OrderItem


class CreateOrderInput(BaseModel):
    """Accept raw payloads from the LLM while ensuring flexible parsing."""
    customer_id: Any = Field(..., description="Customer ID (int or embedded JSON string)")
    items: Any = Field(None, description="List of ordered items or embedded JSON string")


class CreateOrderTool(BaseTool):
    name: str = "create_order"
    description: str = "Create a new order for a customer and update book stock."
    args_schema: Type[BaseModel] = CreateOrderInput

    def _run(self, customer_id: Any, items: Any = None):
        db = SessionLocal()
        try:
            # Handle case: LLM sends everything as a single embedded JSON string
            if isinstance(customer_id, str) and items is None:
                raw = customer_id.strip()
                try:
                    clean = re.sub(r"([{,]\s*)(\w+)\s*:", r'\1"\2":', raw.replace("'", '"'))
                    parsed = json.loads(clean)
                    customer_id = int(parsed.get("customer_id"))
                    items = parsed.get("items", [])
                except Exception as e:
                    return {"error": f"Failed to parse tool input: {e}"}

            # If items is still a string, try to parse it as JSON
            if isinstance(items, str):
                try:
                    items = json.loads(items.replace("'", '"'))
                except Exception as e:
                    return {"error": f"Invalid 'items' format: {e}"}

            # Handle flat input pattern: {"isbn": ..., "qty": ..., "customer_id": ...}
            if not items and isinstance(customer_id, dict):
                if "isbn" in customer_id and ("qty" in customer_id or "quantity" in customer_id):
                    qty_value = customer_id.get("qty") or customer_id.get("quantity")
                    items = [{"isbn": customer_id["isbn"], "qty": qty_value}]
                    customer_id = customer_id.get("customer_id", 1)

            # Handle case where all fields are in stringified JSON
            if not items and "isbn" in str(customer_id):
                try:
                    payload = json.loads(str(customer_id).replace("'", '"'))
                    customer_id = payload.get("customer_id", customer_id)
                    items = [{"isbn": payload.get("isbn"), "qty": payload.get("qty") or payload.get("quantity")}]
                except Exception:
                    pass

            # Ensure valid customer_id
            try:
                customer_id = int(customer_id)
            except Exception:
                return {"error": f"Invalid customer_id: {customer_id}"}

            if not isinstance(items, list):
                return {"error": f"Expected a list for 'items', got {type(items)}"}

            # --- Create order ---
            order = Order(customer_id=customer_id, created_at=datetime.utcnow())
            db.add(order)
            db.flush()

            processed, warnings = [], []

            for item in items:
                isbn = item.get("isbn")
                # Unified qty extraction (accept both qty or quantity)
                raw_qty = item.get("qty") or item.get("quantity") or 0
                try:
                    qty = int(float(str(raw_qty).strip()))
                except Exception:
                    qty = 0

                if not isbn or qty <= 0:
                    warnings.append(f"Invalid entry: {item}")
                    continue

                book = db.query(Book).filter_by(isbn=isbn).first()
                if not book:
                    warnings.append(f"Book '{isbn}' not found — skipped.")
                    continue
                if book.stock < qty:
                    warnings.append(f"Not enough stock for '{book.title}' — skipped.")
                    continue

                db.add(OrderItem(order_id=order.id, isbn=isbn, qty=qty))
                book.stock -= qty
                db.add(book)

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
