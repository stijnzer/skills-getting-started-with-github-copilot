import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
from copy import deepcopy

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Save original state with deep copy
    original_state = deepcopy(activities)
    
    # Run the test
    yield
    
    # Restore original state after test
    activities.clear()
    activities.update(original_state)

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Basketball Team" in data


def test_signup_for_activity():
    activity = "Art Club"
    email = "testuser@example.com"
    # Ensure user is not already signed up
    client.post(f"/activities/{activity}/unregister?email={email}")
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200
    assert f"Signed up {email} for {activity}" in response.json()["message"]
    # Try signing up again (should fail)
    response2 = client.post(f"/activities/{activity}/signup?email={email}")
    assert response2.status_code == 400
    assert "already signed up" in response2.json()["detail"]


def test_unregister_from_activity():
    activity = "Art Club"
    email = "testuser@example.com"
    # Ensure user is signed up
    client.post(f"/activities/{activity}/signup?email={email}")
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200
    assert f"Removed {email} from {activity}" in response.json()["message"]
    # Try unregistering again (should fail)
    response2 = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response2.status_code == 400
    assert "not registered" in response2.json()["detail"]


def test_signup_for_nonexistent_activity():
    """Test that signing up for a non-existent activity returns 404"""
    activity = "Nonexistent Activity"
    email = "testuser@example.com"
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_from_nonexistent_activity():
    """Test that unregistering from a non-existent activity returns 404"""
    activity = "Nonexistent Activity"
    email = "testuser@example.com"
    response = client.post(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_when_activity_is_full():
    """Test that signing up for a full activity returns 400"""
    activity = "Mathletes"  # max_participants: 10
    # Fill the activity to capacity
    for i in range(10):
        email = f"student{i}@example.com"
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
    
    # Try to add one more (should fail)
    email = "overflow@example.com"
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 400
    assert "Activity is full" in response.json()["detail"]


def test_invalid_email_format():
    """Test that invalid email format is rejected"""
    activity = "Art Club"
    invalid_email = "not-an-email"
    response = client.post(f"/activities/{activity}/signup?email={invalid_email}")
    assert response.status_code == 422  # Pydantic validation error
