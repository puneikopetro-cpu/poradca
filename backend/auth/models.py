import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime
from backend.database import Base


class UserRole(str, enum.Enum):
    client = "client"
    advisor = "advisor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.client, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
