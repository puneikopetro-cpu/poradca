from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.service import get_current_user
from backend.auth.models import User
from backend.financial_profile.schemas import FinancialProfileCreate, FinancialProfileOut
from backend.financial_profile import service

router = APIRouter(prefix="/profile", tags=["financial_profile"])


@router.post("", response_model=FinancialProfileOut)
def save_profile(
    data: FinancialProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.upsert_profile(db, current_user.id, data)


@router.get("", response_model=FinancialProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = service.get_profile(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
