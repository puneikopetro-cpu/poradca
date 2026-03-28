"""Tests for /profile endpoints + risk_profile auto-calculation."""
import pytest


class TestSaveProfile:
    def test_create_profile_success(self, client, auth_headers, profile_payload):
        r = client.post("/profile", json=profile_payload, headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["monthly_income"] == 3000.0
        assert data["age"] == 30
        assert data["risk_profile"] is not None

    def test_profile_requires_auth(self, client, profile_payload):
        r = client.post("/profile", json=profile_payload)
        assert r.status_code == 401

    def test_update_existing_profile(self, client, auth_headers, profile_payload):
        client.post("/profile", json=profile_payload, headers=auth_headers)
        updated = {**profile_payload, "monthly_income": 5000.0}
        r = client.post("/profile", json=updated, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["monthly_income"] == 5000.0

    def test_invalid_horizon(self, client, auth_headers, profile_payload):
        bad = {**profile_payload, "investment_horizon": "decade"}
        r = client.post("/profile", json=bad, headers=auth_headers)
        assert r.status_code == 422

    def test_invalid_goal_type(self, client, auth_headers, profile_payload):
        bad = {**profile_payload, "goal_type": "lottery"}
        r = client.post("/profile", json=bad, headers=auth_headers)
        assert r.status_code == 422


class TestGetProfile:
    def test_get_profile_success(self, client, auth_headers, profile_payload):
        client.post("/profile", json=profile_payload, headers=auth_headers)
        r = client.get("/profile", headers=auth_headers)
        assert r.status_code == 200
        assert r.json()["goal_type"] == "retirement"

    def test_get_profile_not_found(self, client, auth_headers):
        r = client.get("/profile", headers=auth_headers)
        assert r.status_code == 404

    def test_get_profile_requires_auth(self, client):
        r = client.get("/profile")
        assert r.status_code == 401


class TestRiskProfileCalculation:
    """Verify that correct risk_profile is assigned after POST /profile."""

    def _post_profile(self, client, auth_headers, **overrides):
        base = {
            "monthly_income": 1200.0,
            "monthly_expenses": 1100.0,
            "total_savings": 500.0,
            "total_debt": 0.0,
            "age": 60,
            "investment_experience": 0,
            "investment_horizon": "short",
            "goal_type": "savings",
        }
        base.update(overrides)
        r = client.post("/profile", json=base, headers=auth_headers)
        assert r.status_code == 200
        return r.json()["risk_profile"]

    def test_conservative_profile(self, client, auth_headers):
        # All low-score inputs → score = 5+5+5+5 = 20 → conservative
        risk = self._post_profile(client, auth_headers)
        assert risk == "conservative"

    def test_balanced_profile(self, client, auth_headers):
        # age=40, cashflow=600, exp=2, horizon=medium → 15+15+15+15 = 60 → balanced
        risk = self._post_profile(
            client, auth_headers,
            age=40,
            monthly_income=2000.0,
            monthly_expenses=1400.0,
            investment_experience=2,
            investment_horizon="medium",
        )
        assert risk == "balanced"

    def test_aggressive_profile(self, client, auth_headers):
        # age=28, cashflow=1500, exp=5, horizon=long → 25+25+25+25 = 100 → aggressive
        risk = self._post_profile(
            client, auth_headers,
            age=28,
            monthly_income=3000.0,
            monthly_expenses=1500.0,
            investment_experience=5,
            investment_horizon="long",
        )
        assert risk == "aggressive"
