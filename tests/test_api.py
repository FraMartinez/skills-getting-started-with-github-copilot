"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data
        assert len(data) > 0

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_activities_have_participants(self):
        """Test that activities have participant lists"""
        response = client.get("/activities")
        data = response.json()
        
        basketball = data["Basketball"]
        assert len(basketball["participants"]) > 0
        assert "alex@mergington.edu" in basketball["participants"]


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant"""
        email = "testuser@mergington.edu"
        
        # Sign up
        response = client.post(f"/activities/Tennis%20Club/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Tennis Club"]["participants"]

    def test_signup_nonexistent_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email(self):
        """Test that duplicate signups are rejected"""
        # First signup
        email = "duplicate@mergington.edu"
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Second signup with same email
        response = client.post(f"/activities/Chess%20Club/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_special_characters_in_email(self):
        """Test signup with special characters in email"""
        email = "user+test@mergington.edu"
        response = client.post(
            f"/activities/Gym%20Class/signup?email={email}"
        )
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unreg@mergington.edu"
        
        # First signup
        client.post(f"/activities/Art%20Studio/signup?email={email}")
        
        # Then unregister
        response = client.post(f"/activities/Art%20Studio/unregister?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "toremove@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Programming%20Class/signup?email={email}")
        
        # Verify signed up
        activities = client.get("/activities").json()
        assert email in activities["Programming Class"]["participants"]
        
        # Unregister
        client.post(f"/activities/Programming%20Class/unregister?email={email}")
        
        # Verify removed
        activities = client.get("/activities").json()
        assert email not in activities["Programming Class"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404

    def test_unregister_not_registered(self):
        """Test unregister when participant is not registered"""
        response = client.post(
            "/activities/Science%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests for multiple operations"""

    def test_signup_and_unregister_flow(self):
        """Test complete flow of signing up and unregistering"""
        email = "flowtest@mergington.edu"
        activity = "Drama%20Club"
        
        # Initial check - user not registered
        activities = client.get("/activities").json()
        assert email not in activities["Drama Club"]["participants"]
        
        # Sign up
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Check signed up
        activities = client.get("/activities").json()
        assert email in activities["Drama Club"]["participants"]
        
        # Unregister
        unreg_response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert unreg_response.status_code == 200
        
        # Check unregistered
        activities = client.get("/activities").json()
        assert email not in activities["Drama Club"]["participants"]

    def test_multiple_users_signup(self):
        """Test multiple users signing up for the same activity"""
        activity = "Debate%20Team"
        users = ["user1@mergington.edu", "user2@mergington.edu", "user3@mergington.edu"]
        
        # Sign up all users
        for user in users:
            response = client.post(f"/activities/{activity}/signup?email={user}")
            assert response.status_code == 200
        
        # Verify all signed up
        activities = client.get("/activities").json()
        for user in users:
            assert user in activities["Debate Team"]["participants"]
