import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

ORIGINAL_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    app_module.activities = copy.deepcopy(ORIGINAL_ACTIVITIES)
    yield
    app_module.activities = copy.deepcopy(ORIGINAL_ACTIVITIES)


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    request_path = "/"
    follow_redirects = False

    # Act
    response = client.get(request_path, follow_redirects=follow_redirects)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(client):
    # Arrange
    request_path = "/activities"

    # Act
    response = client.get(request_path)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_succeeds(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    request_path = f"/activities/{quote(activity_name)}/signup"
    query_params = {"email": email}
    expected_payload = {"message": f"Signed up {email} for {activity_name}"}

    # Act
    response = client.post(request_path, params=query_params)

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_payload
    assert email in app_module.activities[activity_name]["participants"]


def test_duplicate_signup_returns_bad_request(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"
    request_path = f"/activities/{quote(activity_name)}/signup"
    query_params = {"email": existing_email}

    # Act
    response = client.post(request_path, params=query_params)

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_unregister_for_activity_succeeds(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    request_path = f"/activities/{quote(activity_name)}/unregister"
    query_params = {"email": email}
    expected_payload = {"message": f"Removed {email} from {activity_name}"}

    # Act
    response = client.post(request_path, params=query_params)

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_payload
    assert email not in app_module.activities[activity_name]["participants"]


def test_unknown_activity_returns_not_found(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"
    request_path = f"/activities/{quote(activity_name)}/signup"
    query_params = {"email": email}

    # Act
    response = client.post(request_path, params=query_params)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"