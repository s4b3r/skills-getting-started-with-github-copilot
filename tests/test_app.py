from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities_state():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities_returns_seeded_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_adds_participant():
    email = "new.student@mergington.edu"

    response = client.post(f"/activities/Chess%20Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant():
    existing_email = activities["Chess Club"]["participants"][0]

    response = client.post(
        f"/activities/Chess%20Club/signup?email={existing_email}"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_when_activity_is_full():
    activity = activities["Chess Club"]
    activity["max_participants"] = len(activity["participants"])

    response = client.post(
        "/activities/Chess%20Club/signup?email=another.student@mergington.edu"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_participant():
    email = "remove.me@mergington.edu"
    activities["Chess Club"]["participants"].append(email)

    response = client.delete(f"/activities/Chess%20Club/signup?email={email}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_returns_404_for_missing_participant():
    response = client.delete(
        "/activities/Chess%20Club/signup?email=missing@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_signup_returns_404_for_missing_activity():
    response = client.post("/activities/Nonexistent/signup?email=student@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
