#!/usr/bin/env python3
"""Test script to identify type comparison issues in workers."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workers.workers import ClipChooserWorker
import config

def test_type_comparison_issues():
    """Test for potential type comparison issues in workers."""
    
    print("🔍 Testing Type Comparison Issues")
    print("=" * 40)
    
    # Create test worker
    worker = ClipChooserWorker()
    
    # Test scenario 1: Scene with string score (should be float)
    test_scenes_with_string_scores = [
        {
            "start": 0,
            "end": 30,
            "description": "Test scene 1", 
            "score": "0.8",  # STRING instead of FLOAT
            "mood": "neutral"
        },
        {
            "start": 30,
            "end": 60,
            "description": "Test scene 2",
            "score": 0.9,  # Correct FLOAT
            "mood": "intense"
        }
    ]
    
    # Test scenario 2: Scene with string duration (should be numeric)
    test_scenes_with_string_duration = [
        {
            "start": "0",     # STRING instead of number
            "end": "30",      # STRING instead of number  
            "description": "Test scene with string times",
            "score": 0.7,
            "duration": "30"  # STRING instead of number
        }
    ]
    
    # Test scenario 3: Mixed types in scene scoring
    test_scenes_mixed_types = [
        {
            "start": 0,
            "end": 25.5,      # FLOAT end time
            "description": "Mixed type scene",
            "score": "high",  # STRING score (invalid)
            "duration": 25.5
        }
    ]
    
    try:
        print("\n1. Testing scenes with string scores...")
        analysis = {
            "scenes": test_scenes_with_string_scores,
            "total_duration": 120,
            "video_path": "test_video.mp4"
        }
        
        # This should trigger the type comparison issue fix
        result = worker.run(analysis)
        print(f"✅ String score test passed - got {len(result.get('clips', []))} clips")
        
    except Exception as e:
        print(f"❌ String score test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    try:
        print("\n2. Testing scenes with string durations...")
        analysis = {
            "scenes": test_scenes_with_string_duration,
            "total_duration": 60,
            "video_path": "test_video.mp4"
        }
        
        result = worker.run(analysis)
        print(f"✅ String duration test passed - got {len(result.get('clips', []))} clips")
        
    except Exception as e:
        print(f"❌ String duration test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    try:
        print("\n3. Testing scenes with mixed types...")
        analysis = {
            "scenes": test_scenes_mixed_types,
            "total_duration": 30,
            "video_path": "test_video.mp4"
        }
        
        result = worker.run(analysis)
        print(f"✅ Mixed type test passed - got {len(result.get('clips', []))} clips")
        
    except Exception as e:
        print(f"❌ Mixed type test failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    print("\n🎯 Type Comparison Tests Complete!")

if __name__ == "__main__":
    test_type_comparison_issues()
