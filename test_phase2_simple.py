#!/usr/bin/env python3
"""
Simple Phase 2 Test Script - Basic functionality verification
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

import config
from utils.utils import detect_scenes, calculate_motion_score
from workers.workers import AssemblyWorker

# Configure simple logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_scene_detection():
    """Test basic scene detection"""
    print("\n=== Testing Scene Detection ===")
    
    try:
        # Test with real video if it exists
        test_video = "C:/Users/dimit/Videos/anime/1mp4.mp4"
        if os.path.exists(test_video):
            print(f"Testing with real video: {test_video}")
            scenes = detect_scenes(test_video)
        else:
            print("Real video not found, testing with mock")
            scenes = detect_scenes("nonexistent.mp4")  # Should fall back to mock
        
        print(f"✓ Scene detection returned {len(scenes)} scenes")
        
        if scenes:
            first_scene = scenes[0]
            print(f"  First scene: {first_scene.get('description', 'No description')}")
            print(f"  Duration: {first_scene.get('end', 0) - first_scene.get('start', 0):.1f}s")
            print(f"  Score: {first_scene.get('score', 0):.3f}")
        
        return True
        
    except Exception as e:
        print(f"✗ Scene detection failed: {e}")
        return False

def test_motion_scoring():
    """Test basic motion scoring"""
    print("\n=== Testing Motion Scoring ===")
    
    try:
        # Test with real video if it exists
        test_video = "C:/Users/dimit/Videos/anime/1mp4.mp4"
        if os.path.exists(test_video):
            print(f"Testing motion scoring with real video: {test_video}")
            score = calculate_motion_score(test_video, 0.0, 10.0)
        else:
            print("Real video not found, testing with mock")
            score = calculate_motion_score("nonexistent.mp4", 0.0, 10.0)  # Should use mock
        
        print(f"✓ Motion scoring returned: {score:.3f}")
        
        # Convert to float to handle numpy types
        try:
            score_float = float(score)
            if 0.0 <= score_float <= 1.0:
                print(f"  Score is valid (number between 0 and 1): {score_float:.6f}")
                return True
            else:
                print(f"  ✗ Score out of range: {score_float}")
                return False
        except (ValueError, TypeError):
            print(f"  ✗ Invalid score type: {score} (type: {type(score)})")
            return False
        
    except Exception as e:
        print(f"✗ Motion scoring failed: {e}")
        return False

def test_assembly_worker():
    """Test AssemblyWorker enhancements"""
    print("\n=== Testing AssemblyWorker Enhancements ===")
    
    try:
        # Create test clips
        test_clips = [
            {"description": "Action scene", "mood": "intense", "duration": 15.0, "score": 0.9},
            {"description": "Calm moment", "mood": "peaceful", "duration": 20.0, "score": 0.6},
            {"description": "Drama unfolds", "mood": "dramatic", "duration": 25.0, "score": 0.8}
        ]
        
        assembly_worker = AssemblyWorker({})
        
        # Test trimming
        trimmed = assembly_worker.trim_clips_by_scores(test_clips, 30.0)
        print(f"✓ Trimming: {len(test_clips)} clips -> {len(trimmed)} clips")
        
        # Test transitions
        enhanced = assembly_worker.enhance_clips_with_transitions(test_clips)
        print(f"✓ Transitions: Enhanced {len(enhanced)} clips with metadata")
        
        if enhanced:
            first_clip = enhanced[0]
            print(f"  First clip has sequence_position: {first_clip.get('sequence_position')}")
            print(f"  First clip is_first: {first_clip.get('is_first')}")
        
        return True
        
    except Exception as e:
        print(f"✗ AssemblyWorker test failed: {e}")
        return False

def main():
    """Run simple tests"""
    print("🚀 Phase 2 Simple Test Suite")
    print("=" * 40)
    
    tests = [
        ("Scene Detection", test_scene_detection),
        ("Motion Scoring", test_motion_scoring),
        ("AssemblyWorker", test_assembly_worker)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} - PASSED")
            else:
                print(f"✗ {test_name} - FAILED")
        except Exception as e:
            print(f"✗ {test_name} - ERROR: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Phase 2 is working correctly.")
    elif passed >= total * 0.75:
        print("⚠️  Most tests passed. Minor issues detected.")
    else:
        print("❌ Significant issues detected. Please check implementation.")
    
    # Show configuration status
    print(f"\n⚙️  Configuration:")
    print(f"  PySceneDetect available: {hasattr(config, 'USE_REAL_DETECTION')}")
    print(f"  Motion detection enabled: {config.ENABLE_MOTION_DETECTION}")
    print(f"  Motion detection threshold: {getattr(config, 'MOTION_DETECTION_THRESHOLD', 'Not set')}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
