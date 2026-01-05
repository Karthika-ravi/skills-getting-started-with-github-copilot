from fastapi.testclient import TestClient
from copy import deepcopy
import pytest

import src.app as appmod
from src.app import app

client = TestClient(app)

# Keep an original snapshot of the activities so tests are isolated
ORIG = deepcopy(appmod.activities)

@pytest.fixture(autouse=True)
def reset_activities():
    # Restore original activities before each test
    appmod.activities.clear()
    appmod.activities.update(deepcopy(ORIG))
    yield
    # Ensure state is clean after test
    appmod.activities.clear()
    appmod.activities.update(deepcopy(ORIG))


def test_get_activities():
    r = client.get("/activities")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_and_unregister():
    activity = "Chess Club"
    email = "testuser@example.com"

    # Ensure clean start (idempotent)
    client.delete(f"/activities/{activity}/unregister?email={email}")

    # Sign up
    r = client.post(f"/activities/{activity}/signup?email={email}")
    assert r.status_code == 200
    assert f"Signed up {email}" in r.json().get("message", "")

    # Verify participant present
    r2 = client.get("/activities")
    assert email in r2.json()[activity]["participants"]

    # Unregister
    r3 = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert r3.status_code == 200
    assert f"Unregistered {email}" in r3.json().get("message", "")

    # Verify participant removed
    r4 = client.get("/activities")
    assert email not in r4.json()[activity]["participants"]


def test_signup_existing():
    activity = "Chess Club"
    existing = "michael@mergington.edu"
    r = client.post(f"/activities/{activity}/signup?email={existing}")
    assert r.status_code == 400


def test_unregister_nonexistent_activity():
    r = client.delete("/activities/Nonexistent/unregister?email=noone@example.com")
    assert r.status_code == 404
