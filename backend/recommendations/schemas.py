from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
from backend.recommendations.models import RecommendationCategory, RecommendationRiskLevel


class RecommendationOut(BaseModel):
    id: int
    user_id: int
    category: RecommendationCategory
    title: str
    description: str
    expected_return: Optional[float]
    risk_level: RecommendationRiskLevel
    created_at: datetime

    model_config = {"from_attributes": True}
