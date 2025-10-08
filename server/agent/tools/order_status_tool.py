from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Type
import json, re
from server.db import SessionLocal
from server.models import Order, OrderItem, Book


class OrderStatusInput(BaseModel):
    """Accepts flexible payloads for order lookup."""
    order_id: Any = Field(..., description="Order ID (integer or embedded JSON string)")


class OrderStatusTool(BaseTool):
    name: str = "order_status"
    description: str = "Retrieve details and status of a specific order."
    args_schema: Type[BaseModel] = OrderStatusInput

    def _run(self, order_id: Any):
        db = SessionLocal()
        try:
            # --- Normalize the incoming value ---
            if isinstance(order_id, str):
                try:
                    # Handle embedded JSON or loose dict-like input
                    cleaned = re.sub(r"([{,]\s*)(\w+)\s*:", r'\1"\2":', order_id.replace("'", '"'))
                    parsed = json.loads(cleaned)
                    order_id = parsed.get("order_id", order_id)
                except Exception:
                    pass

            try:
                order_id = int(order_id)
            except Exception:
                return {"error": f"Invalid order_id: {order_id}"}

            # --- Fetch the order ---
            order = db.query(Order).filter_by(id=order_id).first()
            if not order:
                return {"error": f"Order {order_id} not found."}

            # --- Fetch items with titles ---
            items = (
                db.query(OrderItem, Book)
                .join(Book, Book.isbn == OrderItem.isbn)
                .filter(OrderItem.order_id == order_id)
                .all()
            )

            order_data = {
                "order_id": order.id,
                "customer_id": order.customer_id,
                "created_at": order.created_at.isoformat(),
                "items": [
                    {"title": b.title, "isbn": b.isbn, "qty": oi.qty, "price": b.price}
                    for oi, b in items
                ],
            }

            return order_data

        except Exception as e:
            db.rollback()
            return {"error": str(e)}

        finally:
            db.close()

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError("Async version not implemented.")
