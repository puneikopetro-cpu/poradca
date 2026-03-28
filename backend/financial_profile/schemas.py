from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from backend.financial_profile.models import InvestmentHorizon, GoalType, RiskProfile


class FinancialProfileCreate(BaseModel):
    monthly_income: float
    monthly_expenses: float
    total_savings: float = 0.0
    total_debt: float = 0.0
    age: int
    investment_experience: int = 0
    investment_horizon: InvestmentHorizon
    goal_type: GoalType


class FinancialProfileOut(BaseModel):
    id: int
    user_id: int
    monthly_income: float
    monthly_expenses: float
    total_savings: float
    total_debt: float
    age: int
    investment_experience: int
    investment_horizon: InvestmentHorizon
    goal_type: GoalType
    risk_profile: Optional[RiskProfile]
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
