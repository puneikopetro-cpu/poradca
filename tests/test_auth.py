"""Tests for /auth endpoints: register, login, me."""
import pytest


class TestRegister:
    def test_register_success(self, client):
        r = client.post("/auth/register", json={
            "email": "new@advisor.sk",
            "password": "strongpass",
            "full_name": "Jan Novak",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["email"] == "new@advisor.sk"
        assert data["full_name"] == "Jan Novak"
        assert data["role"] == "client"
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, registered_user):
        r = client.post("/auth/register", json={
            "email": registered_user["email"],
            "password": "another",
            "full_name": "Duplicate",
        })
        assert r.status_code == 400
        assert "already registered" in r.json()["detail"]

    def test_register_invalid_email(self, client):
        r = client.post("/auth/register", json={
            "email": "not-an-email",
            "password": "pass",
            "full_name": "Bad Email",
        })
        assert r.status_code == 422

    def test_register_missing_fields(self, client):
        r = client.post("/auth/register", json={"email": "x@x.sk"})
        assert r.status_code == 422


class TestLogin:
    def test_login_success(self, client, registered_user):
        r = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        })
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_login_wrong_password(self, client, registered_user):
        r = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "wrongpass",
        })
        assert r.status_code == 401

    def test_login_unknown_email(self, client):
        r = client.post("/auth/login", json={
            "email": "ghost@test.sk",
            "password": "pass",
        })
        assert r.status_code == 401


class TestMe:
    def test_me_returns_current_user(self, client, auth_headers, registered_user):
        r = client.get("/auth/me", headers=auth_headers)
        assert r.status_code == 200
        data = r.json()
        assert data["email"] == registered_user["email"]
        assert data["full_name"] == registered_user["full_name"]

    def test_me_no_token(self, client):
        r = client.get("/auth/me")
        assert r.status_code == 401

    def test_me_invalid_token(self, client):
        r = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert r.status_code == 401
