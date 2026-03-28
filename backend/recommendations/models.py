import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Text, Enum, DateTime, ForeignKey
from backend.database import Base


class RecommendationCategory(str, enum.Enum):
    investment = "investment"
    insurance = "insurance"
    pension = "pension"
    credit = "credit"
    tax = "tax"


class RecommendationRiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(Enum(RecommendationCategory), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    expected_return = Column(Float, nullable=True)
    risk_level = Column(Enum(RecommendationRiskLevel), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
