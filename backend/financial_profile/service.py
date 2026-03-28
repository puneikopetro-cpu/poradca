from sqlalchemy.orm import Session
from backend.financial_profile.models import FinancialProfile
from backend.financial_profile.schemas import FinancialProfileCreate
from backend.risk_engine.scoring import calculate_risk_profile
from backend.logger import get_logger

logger = get_logger(__name__)


def upsert_profile(db: Session, user_id: int, data: FinancialProfileCreate) -> FinancialProfile:
    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    risk = calculate_risk_profile(
        age=data.age,
        monthly_income=data.monthly_income,
        monthly_expenses=data.monthly_expenses,
        investment_experience=data.investment_experience,
        investment_horizon=data.investment_horizon.value,
    )
    action = "updated" if profile else "created"
    if profile:
        for field, value in data.model_dump().items():
            setattr(profile, field, value)
        profile.risk_profile = risk
    else:
        profile = FinancialProfile(
            user_id=user_id,
            risk_profile=risk,
            **data.model_dump(),
        )
        db.add(profile)
    db.commit()
    db.refresh(profile)
    logger.info(
        "Financial profile %s for user_id=%s — risk_profile=%s",
        action, user_id, risk.value,
    )
    return profile


def get_profile(db: Session, user_id: int):
    return db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
