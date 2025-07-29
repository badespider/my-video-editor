import pytest
from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "AI Video Creation API"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_video(sample_video_path):
    with open(sample_video_path, "rb") as video_file:
        response = client.post("/upload/video", files={"file": ("test_video.mp4", video_file, "video/mp4")})
        assert response.status_code == 200
        response_data = response.json()
        assert "session_id" in response_data
        assert response_data["filename"] == "test_video.mp4"


def test_analyze_video_endpoint(mock_session):
    session_id = "mock_session_id"
    sessions = {session_id: mock_session}
    response = client.post(f"/analyze/{session_id}", json={"detailed": True})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "analysis" in response_data


def test_suggestions_endpoint(mock_session):
    session_id = "mock_session_id"
    sessions = {session_id: mock_session}
    response = client.post(f"/suggestions/{session_id}", json={"max_suggestions": 5})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "suggestions" in response_data


def test_optimization_endpoint(mock_session):
    session_id = "mock_session_id"
    sessions = {session_id: mock_session}
    response = client.post(f"/optimize/{session_id}", json={"quality_level": "high"})
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert "recommendations" in response_data

