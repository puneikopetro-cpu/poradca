from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.leads.models import Lead
from backend.leads.schemas import LeadCreate, LeadOut
from backend.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(**data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    logger.info("New lead: %s <%s> interest=%s source=%s", lead.full_name, lead.email, lead.interest, lead.source)
    return lead


@router.get("", response_model=list[LeadOut])
def list_leads(db: Session = Depends(get_db)):
    """Admin endpoint — list all leads."""
    return db.query(Lead).order_by(Lead.created_at.desc()).all()
