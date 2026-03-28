"""SQLAlchemy model for NBS exam questions."""
from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, JSON
from backend.database import Base


class Question(Base):
    __tablename__ = "nbs_questions"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True, nullable=False)
    section = Column(String(200), nullable=False)
    sector = Column(String(100), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)  # zakladny/stredny/vyssi
    text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)   # {"a": "...", "b": "...", ...}
    correct = Column(String(1), nullable=True)
