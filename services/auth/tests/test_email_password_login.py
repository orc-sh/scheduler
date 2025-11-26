import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_login_missing_body_returns_422():
  async with AsyncClient(app=app, base_url="http://test") as ac:
    response = await ac.post("/api/auth/login", json={})
  assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_invalid_credentials_returns_401(monkeypatch):
  from app.services.auth_service import get_auth_service

  auth_service = get_auth_service()

  async def fake_sign_in_with_email(email: str, password: str):  # type: ignore[unused-ignore]
    raise ValueError("Invalid email or password")

  monkeypatch.setattr(auth_service, "sign_in_with_email", fake_sign_in_with_email)

  async with AsyncClient(app=app, base_url="http://test") as ac:
    response = await ac.post(
      "/api/auth/login",
      json={"email": "invalid@example.com", "password": "wrong-password"},
    )

  assert response.status_code == 401
  assert "Invalid email or password" in response.json()["detail"]


