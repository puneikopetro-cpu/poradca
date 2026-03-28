import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime
from backend.database import Base


class LeadInterest(str, enum.Enum):
    investment = "investment"
    mortgage = "mortgage"
    pension = "pension"
    insurance = "insurance"
    tax = "tax"
    other = "other"


class LeadStatus(str, enum.Enum):
    new = "new"
    contacted = "contacted"
    converted = "converted"
    closed = "closed"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    phone = Column(String, nullable=True)
    interest = Column(Enum(LeadInterest), default=LeadInterest.investment)
    message = Column(Text, nullable=True)
    source = Column(String, default="website")
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    created_at = Column(DateTime, default=datetime.utcnow)
