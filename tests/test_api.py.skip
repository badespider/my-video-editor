from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_generate_video():
    request_data = {
        "script": "Test script for video generation",
        "model": "test-model"
    }
    response = client.post("/generate", json=request_data)
    
    # Debug: print response details if it fails
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    response_json = response.json()
    assert "clips" in response_json
    assert "narrations" in response_json
    assert "bgms" in response_json
    assert "timeline" in response_json
    assert "total_duration" in response_json
    assert "assembly_metadata" in response_json
    
    # Verify the data types match expected structure
    assert isinstance(response_json["clips"], dict)
    assert isinstance(response_json["narrations"], dict)
    assert isinstance(response_json["bgms"], dict)
    assert isinstance(response_json["timeline"], list)
    assert isinstance(response_json["total_duration"], (int, float))
    assert isinstance(response_json["assembly_metadata"], dict)


def test_generate_video_with_empty_script():
    """Test API error handling with empty script."""
    request_data = {
        "script": "",
        "model": "test-model"
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 500
    assert "detail" in response.json()


def test_generate_video_with_invalid_request():
    """Test API error handling with invalid request format."""
    # Missing required 'script' field
    request_data = {
        "model": "test-model"
    }
    response = client.post("/generate", json=request_data)
    assert response.status_code == 422  # Validation error
