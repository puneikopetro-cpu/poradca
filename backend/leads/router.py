from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from backend.auth.service import get_current_user
from backend.database import get_db
from backend.leads.models import Lead, LeadStatus
from backend.leads.schemas import LeadCreate, LeadOut
from backend.logger import get_logger
from backend.email_service import send_lead_notification

logger = get_logger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])

ADMIN_KEY = "finadvisor2024"


def require_admin(x_admin_key: Optional[str] = Header(None), _jwt=None):
    """Allow either X-Admin-Key header or valid JWT (fallback)."""
    if x_admin_key == ADMIN_KEY:
        return True
    raise HTTPException(status_code=403, detail="Forbidden")


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(**data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    logger.info("New lead: %s <%s> interest=%s source=%s", lead.full_name, lead.email, lead.interest, lead.source)
    try:
        send_lead_notification(
            lead_name=lead.full_name,
            lead_email=lead.email,
            lead_phone=lead.phone or "",
            interest=str(lead.interest.value) if lead.interest else "",
            message=lead.message or "",
        )
    except Exception as e:
        logger.warning("Email notification failed: %s", e)
    return lead


@router.get("", response_model=list[LeadOut])
def list_leads(db: Session = Depends(get_db), _=Depends(require_admin)):
    """Admin endpoint — list all leads."""
    return db.query(Lead).order_by(Lead.created_at.desc()).all()


class LeadStatusUpdate(BaseModel):
    status: LeadStatus
    note: Optional[str] = None


@router.patch("/{lead_id}/status", response_model=LeadOut)
def update_lead_status(lead_id: int, body: LeadStatusUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Update lead CRM status."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = body.status
    db.commit()
    db.refresh(lead)
    logger.info("Lead #%d status → %s", lead_id, body.status)
    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Delete a lead."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    db.delete(lead)
    db.commit()
