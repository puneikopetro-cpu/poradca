from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from backend.leads.models import LeadInterest, LeadStatus


class LeadCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    interest: LeadInterest = LeadInterest.investment
    message: Optional[str] = None
    source: str = "website"


class LeadOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    interest: LeadInterest
    message: Optional[str]
    source: str
    status: LeadStatus
    created_at: datetime

    model_config = {"from_attributes": True}
