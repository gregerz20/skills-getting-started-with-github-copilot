"""
Integration tests for the Mergington High School Activities API
Using the AAA (Arrange-Act-Assert) testing pattern
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    global activities
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    yield
    activities.clear()


# ========================
# GET /activities Tests
# ========================

def test_get_activities_returns_200(client):
    """Test that GET /activities returns a 200 status code"""
    # Arrange
    # (No setup needed - activities are already initialized by fixture)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200


def test_get_activities_returns_all_activities(client):
    """Test that GET /activities returns all activities"""
    # Arrange
    expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
    expected_count = 3

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    for activity in expected_activities:
        assert activity in data
    assert len(data) == expected_count


def test_get_activities_includes_activity_details(client):
    """Test that activities include all required details"""
    # Arrange
    required_fields = ["description", "schedule", "max_participants", "participants"]

    # Act
    response = client.get("/activities")
    data = response.json()
    chess_club = data["Chess Club"]

    # Assert
    for field in required_fields:
        assert field in chess_club


def test_get_activities_shows_current_participants(client):
    """Test that GET /activities shows current participants"""
    # Arrange
    expected_participant_count = 2
    expected_participant = "michael@mergington.edu"

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    assert len(data["Chess Club"]["participants"]) == expected_participant_count
    assert expected_participant in data["Chess Club"]["participants"]


# ========================
# POST /activities/{name}/signup Tests
# ========================

def test_signup_returns_200_on_success(client):
    """Test that signup returns a 200 status code on success"""
    # Arrange
    new_email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email={new_email}"
    )

    # Assert
    assert response.status_code == 200


def test_signup_adds_participant(client):
    """Test that signup actually adds the participant"""
    # Arrange
    new_email = "newstudent@mergington.edu"
    activity_name = "Chess Club"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    client.post(f"/activities/{activity_name}/signup?email={new_email}")
    response = client.get("/activities")
    data = response.json()

    # Assert
    assert new_email in data[activity_name]["participants"]
    assert len(data[activity_name]["participants"]) == initial_count + 1


def test_signup_returns_success_message(client):
    """Test that signup returns a success message"""
    # Arrange
    new_email = "newstudent@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email={new_email}"
    )
    data = response.json()

    # Assert
    assert "message" in data
    assert new_email in data["message"]
    assert activity_name in data["message"]


def test_signup_for_nonexistent_activity_returns_404(client):
    """Test that signup for a non-existent activity returns 404"""
    # Arrange
    new_email = "newstudent@mergington.edu"
    nonexistent_activity = "Fake Activity"
    expected_status = 404
    expected_detail = "Activity not found"

    # Act
    response = client.post(
        f"/activities/{nonexistent_activity}/signup?email={new_email}"
    )

    # Assert
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail


def test_signup_duplicate_participant_returns_400(client):
    """Test that signing up twice for the same activity returns 400"""
    # Arrange
    existing_email = "michael@mergington.edu"
    activity_name = "Chess Club"
    expected_status = 400

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup?email={existing_email}"
    )

    # Assert
    assert response.status_code == expected_status
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_prevents_duplicate_registration(client):
    """Test that the system actually prevents duplicate registration"""
    # Arrange
    existing_email = "michael@mergington.edu"
    activity_name = "Chess Club"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    client.post(f"/activities/{activity_name}/signup?email={existing_email}")

    # Assert
    assert len(activities[activity_name]["participants"]) == initial_count


def test_signup_different_activities_works(client):
    """Test that a student can sign up for multiple activities"""
    # Arrange
    new_email = "newstudent@mergington.edu"
    activity1 = "Chess Club"
    activity2 = "Programming Class"

    # Act
    response1 = client.post(f"/activities/{activity1}/signup?email={new_email}")
    response2 = client.post(f"/activities/{activity2}/signup?email={new_email}")
    data = client.get("/activities").json()

    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert new_email in data[activity1]["participants"]
    assert new_email in data[activity2]["participants"]


# ========================
# DELETE /activities/{name}/unregister Tests
# ========================

def test_unregister_returns_200_on_success(client):
    """Test that unregister returns 200 on success"""
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )

    # Assert
    assert response.status_code == 200


def test_unregister_removes_participant(client):
    """Test that unregister actually removes the participant"""
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"
    initial_count = len(activities[activity_name]["participants"])

    # Act
    client.delete(f"/activities/{activity_name}/unregister?email={email}")
    data = client.get("/activities").json()

    # Assert
    assert email not in data[activity_name]["participants"]
    assert len(data[activity_name]["participants"]) == initial_count - 1


def test_unregister_returns_success_message(client):
    """Test that unregister returns a success message"""
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={email}"
    )
    data = response.json()

    # Assert
    assert "message" in data
    assert "Unregistered" in data["message"]


def test_unregister_nonexistent_activity_returns_404(client):
    """Test that unregistering from a non-existent activity returns 404"""
    # Arrange
    email = "test@mergington.edu"
    nonexistent_activity = "Fake Activity"
    expected_status = 404

    # Act
    response = client.delete(
        f"/activities/{nonexistent_activity}/unregister?email={email}"
    )

    # Assert
    assert response.status_code == expected_status
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_registered_returns_400(client):
    """Test that unregistering when not registered returns 400"""
    # Arrange
    unregistered_email = "notstudent@mergington.edu"
    activity_name = "Chess Club"
    expected_status = 400

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister?email={unregistered_email}"
    )

    # Assert
    assert response.status_code == expected_status
    assert "not registered" in response.json()["detail"].lower()


def test_unregister_twice_fails_second_time(client):
    """Test that unregistering twice fails the second time"""
    # Arrange
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    # Act - First unregister
    response1 = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert - First unregister succeeds
    assert response1.status_code == 200

    # Act - Second unregister
    response2 = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert - Second unregister fails
    assert response2.status_code == 400


# ========================
# Integration Tests (Multiple Operations)
# ========================

def test_signup_and_unregister_flow(client):
    """Test a complete signup and unregister flow"""
    # Arrange
    email = "integration@mergington.edu"
    activity = "Chess Club"
    initial_count = len(activities[activity]["participants"])

    # Act - Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert - Signup succeeds
    assert signup_response.status_code == 200

    # Act - Verify participant was added
    data = client.get("/activities").json()

    # Assert - Participant added
    assert email in data[activity]["participants"]
    assert len(data[activity]["participants"]) == initial_count + 1

    # Act - Unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert - Unregister succeeds
    assert unregister_response.status_code == 200

    # Act - Verify participant was removed
    data = client.get("/activities").json()

    # Assert - Participant removed
    assert email not in data[activity]["participants"]
    assert len(data[activity]["participants"]) == initial_count


def test_multiple_users_signup_independently(client):
    """Test that multiple users can sign up independently"""
    # Arrange
    activity = "Gym Class"
    test_users = ["user1@test.com", "user2@test.com", "user3@test.com"]

    # Act
    for user_email in test_users:
        response = client.post(f"/activities/{activity}/signup?email={user_email}")
        assert response.status_code == 200

    # Act - Fetch all activities
    data = client.get("/activities").json()

    # Assert - All users are registered
    for user_email in test_users:
        assert user_email in data[activity]["participants"]


def test_participant_count_accuracy(client):
    """Test that participant count stays accurate through operations"""
    # Arrange
    activity = "Programming Class"
    test_email = "test1@test.com"
    initial_data = client.get("/activities").json()
    initial_count = len(initial_data[activity]["participants"])

    # Act - Sign up a new user
    client.post(f"/activities/{activity}/signup?email={test_email}")
    data_after_signup = client.get("/activities").json()

    # Assert - Count increased by 1
    assert len(data_after_signup[activity]["participants"]) == initial_count + 1

    # Act - Unregister the user
    client.delete(f"/activities/{activity}/unregister?email={test_email}")
    data_after_unregister = client.get("/activities").json()

    # Assert - Count returned to initial value
    assert len(data_after_unregister[activity]["participants"]) == initial_count


def test_capacity_tracking(client):
    """Test that available spots are correctly calculated"""
    # Arrange
    activity = "Chess Club"
    max_participants = activities[activity]["max_participants"]
    current_participants = len(activities[activity]["participants"])
    expected_spots_left = max_participants - current_participants

    # Act
    response = client.get("/activities")
    data = response.json()

    # Assert
    actual_spots_left = data[activity]["max_participants"] - len(data[activity]["participants"])
    assert actual_spots_left == expected_spots_left

