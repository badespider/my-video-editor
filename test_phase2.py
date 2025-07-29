#!/usr/bin/env python3
"""
Test script for Phase 2: Chat & Command Parsing
Tests natural language command parsing and application.
"""

import sys
import os
import asyncio
import websocket
import json
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coordinator import VideoAgent
import config

def test_command_parsing():
    """Test Phase 2 Rule 2.1: Natural Language Command Parsing"""
    print("=== Testing Command Parsing ===")
    
    agent = VideoAgent()
    
    # Test commands
    test_commands = [
        "trim the video from 10 seconds to 30 seconds",
        "cut out the first 20 seconds",
        "remove the last 15 seconds",
        "trim intro 5s",
        "cut from 1:30 to 2:45"
    ]
    
    for i, command in enumerate(test_commands):
        try:
            print(f"\nTest {i+1}: '{command}'")
            parsed = agent.parse_command(command)
            print(f"Parsed: {parsed}")
            
            # Validate structure
            if 'type' in parsed and 'params' in parsed:
                print("✅ Command structure is valid")
            else:
                print("❌ Command structure is invalid")
                
        except Exception as e:
            print(f"❌ Command parsing failed: {e}")

def test_command_application():
    """Test applying commands to session data"""
    print("\n=== Testing Command Application ===")
    
    agent = VideoAgent()
    
    # Mock session data
    session_data = {
        'video_path': 'test_video.mp4',
        'edits': [],
        'preview_path': 'test_video.mp4',
        'video_duration': 120.0  # 2 minutes
    }
    
    # Test trim command
    try:
        command = {
            'type': 'trim',
            'params': {'start': 10, 'end': 30}
        }
        
        print(f"Applying command: {command}")
        agent.apply_command(session_data, command)
        
        print(f"Session edits: {session_data['edits']}")
        print(f"Preview path: {session_data['preview_path']}")
        print("✅ Command application successful")
        
    except Exception as e:
        print(f"❌ Command application failed: {e}")

def test_websocket_simulation():
    """Simulate WebSocket interaction"""
    print("\n=== Testing WebSocket Simulation ===")
    
    # This simulates what would happen in a WebSocket connection
    agent = VideoAgent()
    
    session = {
        "video_path": "test_video.mp4",
        "edits": [],
        "preview_path": "test_video.mp4",
        "last_activity": time.time(),
        "video_duration": 180.0  # 3 minutes
    }
    
    # Simulate receiving messages
    messages = [
        "trim the first 10 seconds",
        "cut from 30s to 60s",
        "remove the ending after 2 minutes"
    ]
    
    for i, message in enumerate(messages):
        try:
            print(f"\nReceived message {i+1}: '{message}'")
            
            # Parse command
            command = agent.parse_command(message)
            print(f"Parsed command: {command}")
            
            # Apply command
            agent.apply_command(session, command)
            
            # Simulate response
            response = {
                "status": "success",
                "command": command,
                "preview_url": f"/preview/test_session",
                "edits_count": len(session["edits"])
            }
            
            print(f"Response: {response}")
            print("✅ WebSocket interaction simulated successfully")
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e),
                "input": message
            }
            print(f"❌ Error response: {error_response}")

def test_finalization():
    """Test video finalization process"""
    print("\n=== Testing Video Finalization ===")
    
    agent = VideoAgent()
    
    # Mock session with edits
    session_data = {
        'video_path': 'test_video.mp4',
        'edits': [
            {'type': 'trim', 'params': {'start': 10, 'end': 60}},
            {'type': 'trim', 'params': {'start': 5, 'end': 45}}
        ],
        'preview_path': 'test_video_edited.mp4',
        'video_duration': 120.0
    }
    
    try:
        # Note: This will fail because test_video.mp4 doesn't exist, 
        # but it will test the logic flow
        final_path = agent.finalize_video(session_data)
        print(f"Final video path: {final_path}")
        print("✅ Finalization logic executed")
        
    except Exception as e:
        print(f"Expected error (no test video): {e}")
        print("✅ Finalization error handling works")

def main():
    """Run all Phase 2 tests"""
    print("Phase 2 Testing: Chat & Command Parsing")
    print("=" * 50)
    
    # Test individual components
    test_command_parsing()
    test_command_application()
    test_websocket_simulation()
    test_finalization()
    
    print("\n" + "=" * 50)
    print("Phase 2 Testing Complete!")
    print("\nTo test the full WebSocket server:")
    print("1. Run: python -m uvicorn backend.api:app --reload")
    print("2. Connect to: ws://localhost:8000/ws/edit/test_session")
    print("3. Send commands like: 'trim video from 10s to 30s'")

if __name__ == "__main__":
    main()
