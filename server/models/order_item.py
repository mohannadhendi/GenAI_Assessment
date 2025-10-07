from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from server.db import Base

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    isbn = Column(String, ForeignKey("books.isbn"), nullable=False)
    qty = Column(Integer, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    book = relationship("Book")
