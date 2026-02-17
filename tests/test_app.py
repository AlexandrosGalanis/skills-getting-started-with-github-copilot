"""
Test suite for the High School Activities API.
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint."""

    def test_get_activities(self, client, sample_activities):
        """Test that GET /activities returns a list of activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify structure
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Check that each activity has required fields
        for activity_name, details in activities.items():
            assert isinstance(activity_name, str)
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_activities_have_required_structure(self, client):
        """Test that activities have proper structure."""
        response = client.get("/activities")
        activities = response.json()
        
        # Check specific activity
        assert "Chess Club" in activities
        chess_club = activities["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert isinstance(chess_club["participants"], list)
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignupEndpoint:
    """Tests for the signup endpoint."""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant."""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        assert activity in result["message"]

    def test_signup_updates_participants_list(self, client):
        """Test that signup actually adds participant to the list."""
        email = "testuser@mergington.edu"
        activity = "Basketball Team"
        
        # Get initial state
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"].copy()
        
        # Sign up
        client.post(f"/activities/{activity}/signup", params={"email": email})
        
        # Verify participant was added
        response = client.get("/activities")
        updated_participants = response.json()[activity]["participants"]
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up the same participant twice fails."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for non-existent activity fails."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_signup_requires_email_parameter(self, client):
        """Test that signup requires email parameter."""
        response = client.post("/activities/Chess Club/signup")
        
        # Missing email parameter should result in validation error
        assert response.status_code == 422


class TestUnregisterEndpoint:
    """Tests for the unregister endpoint."""

    def test_unregister_participant(self, client):
        """Test unregistering a participant."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from the list."""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify participant exists
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister", params={"email": email})
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]

    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering a non-existent participant fails."""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "nonexistent@mergington.edu"}
        )
        
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from non-existent activity fails."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"].lower()

    def test_unregister_then_signup_again(self, client):
        """Test that participant can sign up again after unregistering."""
        email = "testuser2@mergington.edu"
        activity = "Tennis Club"
        
        # Sign up
        client.post(f"/activities/{activity}/signup", params={"email": email})
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister", params={"email": email})
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up again should work
        response = client.post(f"/activities/{activity}/signup", params={"email": email})
        assert response.status_code == 200
        
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
