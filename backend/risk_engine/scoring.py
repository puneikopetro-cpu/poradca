"""
Risk Scoring Engine

Factors (0–100 total):
  - Age:                     <35 → 25pts;  35–50 → 15pts;  >50 → 5pts
  - Free cashflow (income-expenses): >1000 → 25pts; 500–1000 → 15pts; <500 → 5pts
  - Investment experience (years):   0 → 5pts;  1–3 → 15pts;  4+ → 25pts
  - Investment horizon:      long → 25pts; medium → 15pts; short → 5pts

Classification:
  0–39  → conservative
  40–69 → balanced
  70–100 → aggressive
"""

from backend.financial_profile.models import RiskProfile


def calculate_risk_profile(
    age: int,
    monthly_income: float,
    monthly_expenses: float,
    investment_experience: int,
    investment_horizon: str,
) -> RiskProfile:
    score = 0

    # Age score
    if age < 35:
        score += 25
    elif age <= 50:
        score += 15
    else:
        score += 5

    # Cashflow score
    cashflow = monthly_income - monthly_expenses
    if cashflow > 1000:
        score += 25
    elif cashflow >= 500:
        score += 15
    else:
        score += 5

    # Experience score
    if investment_experience == 0:
        score += 5
    elif investment_experience <= 3:
        score += 15
    else:
        score += 25

    # Horizon score
    if investment_horizon == "long":
        score += 25
    elif investment_horizon == "medium":
        score += 15
    else:
        score += 5

    # Classify
    if score >= 70:
        return RiskProfile.aggressive
    elif score >= 40:
        return RiskProfile.balanced
    else:
        return RiskProfile.conservative
