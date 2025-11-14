"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for the /activities GET endpoint"""
    
    def test_get_activities_success(self):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
            
    def test_activities_contain_expected_activities(self):
        """Test that known activities are in the response"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club"
        ]
        for activity in expected_activities:
            assert activity in data


class TestSignupEndpoint:
    """Tests for the /activities/{activity_name}/signup POST endpoint"""
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        
        # Get initial participant count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Get updated participant count
        response = client.get("/activities")
        updated_count = len(response.json()["Chess Club"]["participants"])
        assert updated_count == initial_count + 1
        assert email in response.json()["Chess Club"]["participants"]
        
    def test_signup_duplicate_email(self):
        """Test that signing up with duplicate email fails"""
        email = "duplicate@mergington.edu"
        
        # First signup
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        
    def test_signup_nonexistent_activity(self):
        """Test signup fails for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the /activities/{activity_name}/unregister DELETE endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        email = "unreg@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Drama%20Club/signup?email={email}")
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Drama Club"]["participants"]
        
        # Then unregister
        response = client.delete(
            f"/activities/Drama%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Drama Club" in data["message"]
        
    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove@mergington.edu"
        
        # Sign up first
        client.post(f"/activities/Art%20Club/signup?email={email}")
        
        # Verify added
        response = client.get("/activities")
        assert email in response.json()["Art Club"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Art%20Club/unregister?email={email}")
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Art Club"]["participants"]
        
    def test_unregister_nonexistent_activity(self):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
        
    def test_unregister_not_registered(self):
        """Test unregister fails when participant is not registered"""
        email = "notregistered@mergington.edu"
        response = client.delete(
            f"/activities/Robotics%20Club/unregister?email={email}"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests for the full workflow"""
    
    def test_signup_and_unregister_workflow(self):
        """Test the complete workflow of signing up and unregistering"""
        email = "workflow@mergington.edu"
        activity = "Debate Team"
        
        # Initial state: verify email is not in participants
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Sign up
        response = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity.replace(' ', '%20')}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
