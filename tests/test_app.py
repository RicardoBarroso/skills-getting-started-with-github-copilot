from copy import deepcopy
from pathlib import Path
import sys
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    # Arrange
    original_activities = deepcopy(activities)

    yield

    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app)


def test_root_redirects_to_static_page(client):
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == activities


def test_signup_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_participant_when_activity_is_full(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student{i}@mergington.edu"
        for i in range(activity["max_participants"])
    ]

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert email not in activity["participants"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name, safe='')}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_participant_who_is_not_signed_up(client):
    # Arrange
    activity_name = "Chess Club"
    email = "not.signed.up@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name, safe='')}/participants/{quote(email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not signed up for this activity"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
