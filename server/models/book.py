from sqlalchemy import Column, String, Integer, Float
from server.db import Base

class Book(Base):
    __tablename__ = "books"

    isbn = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
