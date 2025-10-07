import json
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.db import SessionLocal
from server.models import Book, Customer, Order, OrderItem

def seed_database():
    db = SessionLocal()
    with open("db/seed_data.json", "r") as f:
        data = json.load(f)

    # Seed Books
    for b in data["books"]:
        if not db.query(Book).filter_by(isbn=b["isbn"]).first():
            db.add(Book(**b))

    # Seed Customers
    for c in data["customers"]:
        if not db.query(Customer).filter_by(email=c["email"]).first():
            db.add(Customer(**c))

    db.commit()

    # Seed Orders
    for o in data["orders"]:
        db.add(Order(**o))
    db.commit()

    # Seed Order Items
    for oi in data["order_items"]:
        db.add(OrderItem(**oi))
    db.commit()

    db.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_database()
