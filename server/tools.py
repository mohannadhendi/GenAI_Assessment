from sqlalchemy.orm import Session
from fastapi import HTTPException
from server.models import Book, Order, OrderItem, Customer
from datetime import datetime


# find_books by title or author
def find_books(db: Session, q: str, by: str = "title"):

    """
    SQL Equivalent:
    -- Search by title or author (case-insensitive)

    SELECT isbn, title, author, price, stock
    FROM books
    WHERE title ILIKE '%{q}%';
    OR
    SELECT isbn, title, author, price, stock
    FROM books
    WHERE author ILIKE '%{q}%';
    """
    
    """
    Search for books by title or author.
    Supports multiple titles separated by commas or 'and'.
    Example:
        q = "Clean Code, Refactoring"
    """
    if by not in ["title", "author"]:
        raise ValueError("Search 'by' must be 'title' or 'author'")

    # Split queries (by comma or 'and')
    parts = [p.strip() for p in q.replace(" and ", ",").split(",") if p.strip()]
    results = []

    for term in parts:
        matches = db.query(Book).filter(getattr(Book, by).ilike(f"%{term}%")).all()
        for b in matches:
            results.append({
                "isbn": b.isbn,
                "title": b.title,
                "author": b.author,
                "price": b.price,
                "stock": b.stock
            })

    return results




# create_order
def create_order(db: Session, customer_id: int, items: list[dict]):
    """
    Create a new order for a customer.
    Each item can contain either:
        - title: book title
        - isbn: book ISBN (optional)
    Example items:
        [{"title": "Clean Code", "qty": 2}, {"title": "Refactoring", "qty": 1}]
    """

    order = Order(customer_id=customer_id, created_at=datetime.utcnow())
    db.add(order)
    db.flush()  # generates order.id

    results = []
    warnings = []

    for item in items:
        # extract title or isbn
        isbn = item.get("isbn")
        title = item.get("title")
        qty = item.get("qty", 1)

        # Try to find the book either by ISBN or by title
        query = db.query(Book)
        if isbn:
            book = query.filter(Book.isbn == isbn).first()
        elif title:
            book = query.filter(Book.title.ilike(f"%{title}%")).first()
        else:
            warnings.append("Item missing both 'title' and 'isbn' — skipped.")
            continue

        if not book:
            warnings.append(f"Book '{title or isbn}' not found — skipped.")
            continue

        # Check stock
        if book.stock < qty:
            warnings.append(f"Not enough stock for '{book.title}'. Requested {qty}, available {book.stock}.")
            continue

        # 🧾 Add order item and update stock
        db.add(OrderItem(order_id=order.id, isbn=book.isbn, qty=qty))
        book.stock -= qty
        results.append({"title": book.title, "remaining_stock": book.stock})

    # If no valid books were found → cancel the order
    if not results:
        db.rollback()
        raise ValueError("No valid books found to create the order.")

    db.commit()
    db.refresh(order)

    # Return results in readable format
    return {
        "order_id": order.id,
        "items": results,
        "warnings": warnings if warnings else None
    }

# restock_book
def restock_book(db: Session, isbn: str, qty: int):

    """
    SQL Equivalent:
    UPDATE books
    SET stock = stock + {qty}
    WHERE isbn = '{isbn}'
    RETURNING stock;
    """

    book = db.get(Book, isbn)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    book.stock += qty
    db.commit()
    return {"isbn": isbn, "new_stock": book.stock}


# update_price
def update_price(db: Session, isbn: str, price: float):

    """
    SQL Equivalent:
    UPDATE books
    SET price = {price}
    WHERE isbn = '{isbn}'
    RETURNING price;
    """

    book = db.get(Book, isbn)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
    book.price = price
    db.commit()
    return {"isbn": isbn, "updated_price": price}


# order_status
def order_status(db: Session, order_id: int):
    
    """
    SQL Equivalent:
    SELECT 
        o.id AS order_id,
        c.name AS customer_name,
        b.title AS book_title,
        oi.qty,
        o.created_at
    FROM orders o
    JOIN customers c ON c.id = o.customer_id
    JOIN order_items oi ON oi.order_id = o.id
    JOIN books b ON b.isbn = oi.isbn
    WHERE o.id = {order_id};
    """

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")

    items = (
        db.query(OrderItem, Book)
        .join(Book, Book.isbn == OrderItem.isbn)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    return {
        "order_id": order.id,
        "customer_id": order.customer_id,
        "items": [{"title": book.title, "qty": item.qty} for item, book in items],
        "created_at": order.created_at
    }


# inventory_summary
def inventory_summary(db: Session, threshold: int = 5):

    """
    SQL Equivalent:
    SELECT isbn, title, author, stock
    FROM books
    WHERE stock <= {threshold}
    ORDER BY stock ASC;
    """

    books = db.query(Book).filter(Book.stock <= threshold).all()
    return [{"isbn": b.isbn, "title": b.title, "stock": b.stock} for b in books]
