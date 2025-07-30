#!/usr/bin/env python3
"""
Test CORS configuration for video upload
"""

import requests
import json
import io

def test_cors_preflight():
    """Test CORS preflight request"""
    headers = {
        'Origin': 'http://localhost:5173',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        response = requests.options('http://127.0.0.1:8000/upload/video', headers=headers)
        print(f"CORS Preflight Status: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
        
        cors_allow_origin = response.headers.get('Access-Control-Allow-Origin')
        cors_allow_methods = response.headers.get('Access-Control-Allow-Methods')
        
        if cors_allow_origin:
            print(f"✅ CORS Origin Allowed: {cors_allow_origin}")
        else:
            print("❌ CORS Origin not set")
            
        if cors_allow_methods:
            print(f"✅ CORS Methods Allowed: {cors_allow_methods}")
        else:
            print("❌ CORS Methods not set")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ CORS preflight test failed: {e}")
        return False

def test_upload_with_origin():
    """Test upload with Origin header"""
    video_content = b"fake video content for testing"
    video_file = io.BytesIO(video_content)
    
    files = {
        'file': ('test_video.mp4', video_file, 'video/mp4')
    }
    
    headers = {
        'Origin': 'http://localhost:5173'
    }
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/upload/video',
            files=files,
            headers=headers,
            timeout=10
        )
        
        print(f"Upload with Origin Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Upload with CORS successful!")
            print(f"Session ID: {result.get('session_id')}")
            return True
        else:
            print(f"❌ Upload failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload with origin test failed: {e}")
        return False

if __name__ == "__main__":
    print("🌐 Testing CORS Configuration")
    print("=" * 40)
    
    print("\n1. Testing CORS preflight...")
    test_cors_preflight()
    
    print("\n2. Testing upload with Origin header...")
    test_upload_with_origin()
    
    print("\n" + "=" * 40)
    print("CORS test completed!")
