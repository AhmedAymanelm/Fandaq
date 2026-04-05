import os
import re
import subprocess
from datetime import date

import httpx
import pytest


BASE_URL = os.getenv("SMOKE_BASE_URL", "http://127.0.0.1:8000")
SMOKE_USER = os.getenv("SMOKE_USERNAME", "admin")
SMOKE_PASS = os.getenv("SMOKE_PASSWORD", "rosegate2024")


def _extract_revision(text: str) -> str | None:
    match = re.search(r"([0-9a-f]{12})", text)
    return match.group(1) if match else None


@pytest.mark.smoke
def test_migration_head_matches_current():
    """Smoke: DB migration is on latest head."""
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    alembic_cmd = os.path.join(repo, "venv", "bin", "alembic")
    if not os.path.exists(alembic_cmd):
        alembic_cmd = "alembic"

    heads = subprocess.check_output([alembic_cmd, "-c", os.path.join(repo, "alembic.ini"), "heads"], text=True)
    current = subprocess.check_output([alembic_cmd, "-c", os.path.join(repo, "alembic.ini"), "current"], text=True)

    head_rev = _extract_revision(heads)
    current_rev = _extract_revision(current)

    assert head_rev, f"Could not parse head revision from output: {heads}"
    assert current_rev, f"Could not parse current revision from output: {current}"
    assert current_rev == head_rev, f"DB revision mismatch: current={current_rev}, head={head_rev}"


@pytest.mark.smoke
def test_login_smoke():
    """Smoke: login endpoint returns token and user."""
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"username": SMOKE_USER, "password": SMOKE_PASS},
            )
    except Exception as exc:
        pytest.skip(f"Server is not reachable for smoke login test: {exc}")

    assert response.status_code == 200, f"Login failed: {response.status_code} {response.text}"
    payload = response.json()
    assert payload.get("access_token"), "Missing access token in login response"
    assert payload.get("user"), "Missing user in login response"


@pytest.mark.smoke
def test_report_send_smoke():
    """Smoke: send-report endpoint is reachable and behaves gracefully."""
    try:
        with httpx.Client(timeout=30.0) as client:
            login = client.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"username": SMOKE_USER, "password": SMOKE_PASS},
            )
    except Exception as exc:
        pytest.skip(f"Server is not reachable for smoke report test: {exc}")

    if login.status_code != 200:
        pytest.skip(f"Login unavailable for smoke report test: {login.status_code} {login.text}")

    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    with httpx.Client(timeout=30.0) as client:
        hotels_resp = client.get(f"{BASE_URL}/api/v1/hotels", headers=headers)
        assert hotels_resp.status_code == 200, f"Hotels list failed: {hotels_resp.status_code} {hotels_resp.text}"

        hotels = hotels_resp.json().get("hotels", [])
        assert hotels, "No hotels found for smoke report test"
        hotel_id = hotels[0]["id"]

        send_resp = client.post(
            f"{BASE_URL}/api/v1/hotels/{hotel_id}/daily-pricing/send-report",
            params={"date": date.today().isoformat()},
            headers=headers,
        )

    # 200 = sent, 400 = controlled business error (e.g., no pricing/SMTP config).
    assert send_resp.status_code in (200, 400), (
        f"Unexpected send-report status: {send_resp.status_code} {send_resp.text}"
    )
