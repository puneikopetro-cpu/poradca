from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.service import get_current_user
from backend.auth.models import User
from backend.financial_profile.service import get_profile
from backend.recommendations.schemas import RecommendationOut
from backend.recommendations import service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationOut])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Financial profile not found. Please complete /profile first.")
    if not profile.risk_profile:
        raise HTTPException(status_code=400, detail="Risk profile not calculated yet.")

    return service.generate_recommendations(db, current_user.id, profile.risk_profile, profile.goal_type)
