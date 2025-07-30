#!/usr/bin/env python3
"""
Test script to verify video upload functionality
"""

import requests
import json
import io

def test_video_upload():
    """Test the video upload endpoint"""
    
    # Create a simple mock video file content (just some bytes)
    video_content = b"fake video content for testing"
    
    # Create a file-like object
    video_file = io.BytesIO(video_content)
    
    # Prepare the upload
    files = {
        'file': ('test_video.mp4', video_file, 'video/mp4')
    }
    
    try:
        # Make the upload request
        response = requests.post(
            'http://127.0.0.1:8000/upload/video',
            files=files,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload successful!")
            print(f"Session ID: {result.get('session_id')}")
            print(f"Filename: {result.get('filename')}")
            print(f"WebSocket Token: {result.get('ws_token')}")
            return True
        else:
            print("❌ Upload failed!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return False

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        print(f"Health check status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Server is healthy")
            return True
        else:
            print("⚠️ Server health check failed")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get('http://127.0.0.1:8000/', timeout=5)
        print(f"Root endpoint status: {response.status_code}")
        print(f"Root response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing AI Video Editor API Endpoints")
    print("=" * 50)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    test_root_endpoint()
    
    # Test 2: Health check
    print("\n2. Testing health check...")
    test_health_check()
    
    # Test 3: Video upload
    print("\n3. Testing video upload...")
    test_video_upload()
    
    print("\n" + "=" * 50)
    print("Test completed!")
