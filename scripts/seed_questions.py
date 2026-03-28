"""Seed NBS questions from JSON into the database."""
from __future__ import annotations
import json
import sys
import os

# Allow running as: python3 scripts/seed_questions.py
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database import SessionLocal, engine, Base
import backend.quiz.models  # noqa — register model
from backend.quiz.models import Question

def main():
    json_path = os.path.join(os.path.dirname(__file__), "questions.json")
    with open(json_path, encoding="utf-8") as f:
        questions = json.load(f)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Question).count()
        if existing >= len(questions):
            print(f"Already have {existing} questions. Skipping seed.")
            return

        db.query(Question).delete()
        for q in questions:
            db.add(Question(
                number=q["number"],
                section=q["section"],
                sector=q["sector"],
                level=q["level"],
                text=q["text"],
                options=q["options"],
                correct=q["correct"],
            ))
        db.commit()
        print(f"Seeded {len(questions)} questions.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
