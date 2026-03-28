"""Quiz API router — random questions for NBS exam prep."""
from __future__ import annotations
import random
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db
from backend.quiz.models import Question

router = APIRouter(prefix="/quiz", tags=["quiz"])


class QuestionOut(BaseModel):
    id: int
    number: int
    section: str
    sector: str
    level: str
    text: str
    options: dict
    correct: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/question/random", response_model=QuestionOut)
def random_question(
    sector: Optional[str] = Query(None, description="Filter by sector slug"),
    level: Optional[str] = Query(None, description="zakladny / stredny / vyssi"),
    db: Session = Depends(get_db),
):
    """Return a random NBS exam question."""
    q = db.query(Question)
    if sector:
        q = q.filter(Question.sector.ilike(f"%{sector}%"))
    if level:
        q = q.filter(Question.level == level)
    ids = [r.id for r in q.with_entities(Question.id).all()]
    if not ids:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No questions found")
    chosen_id = random.choice(ids)
    return db.query(Question).get(chosen_id)


@router.get("/question/{number}", response_model=QuestionOut)
def get_question(number: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.number == number).first()
    if not q:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@router.get("/sectors")
def list_sectors(db: Session = Depends(get_db)):
    rows = db.query(Question.sector).distinct().all()
    return {"sectors": [r[0] for r in rows]}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(Question).count()
    by_sector = {}
    for sector, count in db.query(Question.sector, db.query(Question).filter(
            Question.sector == Question.sector).count.__class__):
        pass
    # Simple approach
    from sqlalchemy import func
    rows = db.query(Question.sector, func.count(Question.id)).group_by(Question.sector).all()
    return {
        "total": total,
        "by_sector": {r[0]: r[1] for r in rows},
    }
