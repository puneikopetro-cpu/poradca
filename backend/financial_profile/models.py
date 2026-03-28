import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, Enum, DateTime, ForeignKey
from backend.database import Base


class InvestmentHorizon(str, enum.Enum):
    short = "short"
    medium = "medium"
    long = "long"


class GoalType(str, enum.Enum):
    savings = "savings"
    retirement = "retirement"
    property = "property"
    education = "education"
    growth = "growth"


class RiskProfile(str, enum.Enum):
    conservative = "conservative"
    balanced = "balanced"
    aggressive = "aggressive"


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    monthly_income = Column(Float, nullable=False)
    monthly_expenses = Column(Float, nullable=False)
    total_savings = Column(Float, default=0.0)
    total_debt = Column(Float, default=0.0)
    age = Column(Integer, nullable=False)
    investment_experience = Column(Integer, default=0)
    investment_horizon = Column(Enum(InvestmentHorizon), nullable=False)
    goal_type = Column(Enum(GoalType), nullable=False)
    risk_profile = Column(Enum(RiskProfile), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
