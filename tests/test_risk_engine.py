"""Unit tests for risk_engine/scoring.py — no DB needed."""
import pytest
from backend.risk_engine.scoring import calculate_risk_profile
from backend.financial_profile.models import RiskProfile


def score(age, income, expenses, experience, horizon):
    return calculate_risk_profile(
        age=age,
        monthly_income=income,
        monthly_expenses=expenses,
        investment_experience=experience,
        investment_horizon=horizon,
    )


class TestRiskScoreConservative:
    def test_all_minimum_factors(self):
        # 5+5+5+5 = 20
        assert score(60, 1200, 1100, 0, "short") == RiskProfile.conservative

    def test_age_over_50(self):
        assert score(55, 3000, 1500, 5, "long") != RiskProfile.conservative

    def test_boundary_score_30(self):
        # age=55(5) + cashflow=420(5) + exp=0(5) + horizon=medium(15) = 30 → conservative
        result = score(55, 1020, 600, 0, "medium")
        assert result == RiskProfile.conservative


class TestRiskScoreBalanced:
    def test_all_medium_factors(self):
        # 15+15+15+15 = 60
        assert score(40, 2000, 1400, 2, "medium") == RiskProfile.balanced

    def test_boundary_score_40(self):
        # 5+5+5+25 = 40 → balanced
        assert score(60, 1200, 1100, 0, "long") == RiskProfile.balanced

    def test_boundary_score_69(self):
        # 25+25+5+15 = 70 → aggressive, so 25+15+15+15=70 → aggressive
        # 25+15+15+14 not possible; try 25+5+15+25=70 → aggressive
        # For 69: not achievable with discrete 5/15/25 steps → skip
        pass


class TestRiskScoreAggressive:
    def test_all_maximum_factors(self):
        # 25+25+25+25 = 100
        assert score(30, 3000, 1500, 5, "long") == RiskProfile.aggressive

    def test_boundary_score_70(self):
        # 25+25+15+5 = 70 → aggressive
        assert score(30, 3000, 1500, 2, "short") == RiskProfile.aggressive

    def test_young_high_cashflow_long_horizon(self):
        assert score(25, 5000, 1000, 0, "long") == RiskProfile.aggressive


class TestRiskScoreEdgeCases:
    def test_age_exactly_35(self):
        # age=35 → 35–50 bucket → 15pts
        result = score(35, 3000, 1500, 5, "long")
        # 15+25+25+25 = 90 → aggressive
        assert result == RiskProfile.aggressive

    def test_age_exactly_50(self):
        # age=50 → 35–50 bucket → 15pts
        result = score(50, 3000, 1500, 5, "long")
        assert result == RiskProfile.aggressive

    def test_cashflow_exactly_500(self):
        # cashflow=500 → 500–1000 bucket → 15pts
        result = score(30, 2500, 2000, 5, "long")
        # 25+15+25+25 = 90 → aggressive
        assert result == RiskProfile.aggressive

    def test_cashflow_exactly_1000(self):
        # cashflow=1000 → >1000? No. 1000 is not > 1000 → medium bucket (500–1000)
        result = score(30, 2500, 1500, 5, "long")
        # cashflow=1000 → 15pts; 25+15+25+25 = 90 → aggressive
        assert result == RiskProfile.aggressive

    def test_negative_cashflow_still_scores(self):
        # cashflow < 500 → 5pts
        result = score(60, 800, 1200, 0, "short")
        # 5+5+5+5 = 20 → conservative
        assert result == RiskProfile.conservative

    def test_experience_exactly_3(self):
        # exp=3 → 1–3 bucket → 15pts
        result = score(60, 1200, 1100, 3, "short")
        # 5+5+15+5 = 30 → conservative
        assert result == RiskProfile.conservative

    def test_experience_exactly_4(self):
        # exp=4 → 4+ bucket → 25pts
        result = score(60, 1200, 1100, 4, "short")
        # 5+5+25+5 = 40 → balanced
        assert result == RiskProfile.balanced

    @pytest.mark.parametrize("horizon,expected_pts", [
        ("short", 5),
        ("medium", 15),
        ("long", 25),
    ])
    def test_all_horizons(self, horizon, expected_pts):
        # Use other factors fixed at max → total = 75 + expected_pts
        result = score(30, 3000, 1500, 5, horizon)
        # 25+25+25+pts; all >= 40 → at minimum balanced
        assert result in (RiskProfile.balanced, RiskProfile.aggressive)
