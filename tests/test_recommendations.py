"""Tests for GET /recommendations endpoint."""
import pytest


def create_profile(client, auth_headers, goal_type="growth", horizon="long",
                   age=28, income=3000.0, expenses=1500.0, experience=5):
    payload = {
        "monthly_income": income,
        "monthly_expenses": expenses,
        "total_savings": 10000.0,
        "total_debt": 0.0,
        "age": age,
        "investment_experience": experience,
        "investment_horizon": horizon,
        "goal_type": goal_type,
    }
    r = client.post("/profile", json=payload, headers=auth_headers)
    assert r.status_code == 200
    return r.json()["risk_profile"]


class TestRecommendations:
    def test_recommendations_require_auth(self, client):
        r = client.get("/recommendations")
        assert r.status_code == 401

    def test_recommendations_require_profile(self, client, auth_headers):
        r = client.get("/recommendations", headers=auth_headers)
        assert r.status_code == 404

    def test_recommendations_returned_as_list(self, client, auth_headers):
        create_profile(client, auth_headers)
        r = client.get("/recommendations", headers=auth_headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    def test_recommendation_fields_present(self, client, auth_headers):
        create_profile(client, auth_headers)
        r = client.get("/recommendations", headers=auth_headers)
        rec = r.json()[0]
        for field in ("id", "user_id", "category", "title", "description", "risk_level"):
            assert field in rec, f"Missing field: {field}"

    def test_conservative_retirement_includes_dds(self, client, auth_headers):
        """Conservative + retirement → should include III. pilier (DDS)."""
        risk = create_profile(
            client, auth_headers,
            goal_type="retirement", horizon="short",
            age=60, income=1200.0, expenses=1100.0, experience=0,
        )
        assert risk == "conservative"
        r = client.get("/recommendations", headers=auth_headers)
        titles = [rec["title"] for rec in r.json()]
        assert any("III. pilier" in t or "DDS" in t for t in titles)

    def test_aggressive_growth_includes_etf(self, client, auth_headers):
        """Aggressive + growth → should include ETF or stocks."""
        risk = create_profile(
            client, auth_headers,
            goal_type="growth", horizon="long",
            age=28, income=3000.0, expenses=1500.0, experience=5,
        )
        assert risk == "aggressive"
        r = client.get("/recommendations", headers=auth_headers)
        titles = [rec["title"] for rec in r.json()]
        assert any("ETF" in t or "akci" in t.lower() for t in titles)

    def test_property_goal_includes_hypoteka(self, client, auth_headers):
        """Any risk + property → should include hypotéka."""
        create_profile(client, auth_headers, goal_type="property")
        r = client.get("/recommendations", headers=auth_headers)
        titles = [rec["title"] for rec in r.json()]
        assert any("hypot" in t.lower() or "Hypot" in t for t in titles)

    def test_savings_goal_includes_terminovany_vklad(self, client, auth_headers):
        create_profile(client, auth_headers, goal_type="savings")
        r = client.get("/recommendations", headers=auth_headers)
        titles = [rec["title"] for rec in r.json()]
        assert any("vklad" in t.lower() or "Money Market" in t for t in titles)

    def test_no_duplicate_recommendations(self, client, auth_headers):
        create_profile(client, auth_headers)
        r = client.get("/recommendations", headers=auth_headers)
        titles = [rec["title"] for rec in r.json()]
        assert len(titles) == len(set(titles)), "Duplicate recommendations found"

    def test_recommendations_refreshed_after_profile_update(self, client, auth_headers):
        """After updating profile, /recommendations should reflect new risk_profile."""
        create_profile(client, auth_headers, goal_type="retirement", horizon="long",
                       age=28, income=3000.0, expenses=1500.0, experience=5)
        r1 = client.get("/recommendations", headers=auth_headers)
        titles_before = {rec["title"] for rec in r1.json()}

        # Switch to conservative profile
        create_profile(client, auth_headers, goal_type="retirement", horizon="short",
                       age=65, income=1200.0, expenses=1100.0, experience=0)
        r2 = client.get("/recommendations", headers=auth_headers)
        titles_after = {rec["title"] for rec in r2.json()}

        assert titles_before != titles_after
