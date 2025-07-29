#!/usr/bin/env python3
"""
Test script for Phase 1 Rule 1.1: Enhanced Real Scene Detection
Tests the updated scene detection with min_scene_len and adaptive thresholds.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.utils import detect_scenes, get_video_info
import config

def test_enhanced_scene_detection():
    """Test the enhanced scene detection functionality."""
    print("=== Phase 1 Rule 1.1: Enhanced Real Scene Detection Test ===\n")
    
    # Test video path
    test_video = r"C:\Users\dimit\Videos\anime\1mp4.mp4"
    
    print(f"Testing enhanced scene detection on: {test_video}")
    print(f"Real detection enabled: {config.USE_REAL_DETECTION}")
    print(f"Scene detection threshold: {config.SCENE_DETECTION_THRESHOLD}")
    print(f"Minimum scene duration: {config.MIN_SCENE_DURATION}s")
    print(f"Motion detection enabled: {config.ENABLE_MOTION_DETECTION}")
    print()
    
    # Get video info first
    print("1. Getting video information...")
    video_info = get_video_info(test_video)
    print(f"   Video duration: {video_info.get('duration', 'Unknown')}s")
    print(f"   Video FPS: {video_info.get('fps', 'Unknown')}")
    print(f"   Video resolution: {video_info.get('resolution', 'Unknown')}")
    print(f"   Has audio: {video_info.get('has_audio', 'Unknown')}")
    print()
    
    # Test scene detection
    print("2. Running enhanced scene detection...")
    try:
        scenes = detect_scenes(test_video)
        
        print(f"   Detected {len(scenes)} scenes")
        print()
        
        # Analyze the results
        if scenes:
            print("3. Scene Analysis Results:")
            total_coverage = 0
            for i, scene in enumerate(scenes[:5]):  # Show first 5 scenes
                duration = scene.get('end', 0) - scene.get('start', 0)
                total_coverage += duration
                
                print(f"   Scene {i+1}:")
                print(f"     Time: {scene.get('start', 0):.1f}s - {scene.get('end', 0):.1f}s ({duration:.1f}s)")
                print(f"     Description: {scene.get('description', 'N/A')}")
                print(f"     Mood: {scene.get('mood', 'N/A')}")
                print(f"     Score: {scene.get('score', 0):.3f}")
                
                if 'motion_score' in scene:
                    print(f"     Motion Score: {scene['motion_score']:.3f}")
                if 'detection_method' in scene:
                    print(f"     Detection Method: {scene['detection_method']}")
                if 'threshold_used' in scene:
                    print(f"     Threshold Used: {scene['threshold_used']}")
                print()
            
            if len(scenes) > 5:
                print(f"   ... and {len(scenes) - 5} more scenes")
                print()
            
            # Coverage analysis
            video_duration = video_info.get('duration', 0)
            if video_duration > 0:
                coverage_percent = (total_coverage / video_duration) * 100
                print(f"4. Coverage Analysis:")
                print(f"   Total scene coverage: {total_coverage:.1f}s / {video_duration:.1f}s ({coverage_percent:.1f}%)")
                print(f"   Coverage requirement: {config.COVERAGE_REQUIREMENT * 100:.0f}%")
                
                if coverage_percent >= config.COVERAGE_REQUIREMENT * 100:
                    print("   ✅ Coverage requirement MET")
                else:
                    print("   ❌ Coverage requirement NOT met")
                print()
            
            # Quality metrics
            print("5. Quality Metrics:")
            avg_scene_duration = sum(s.get('end', 0) - s.get('start', 0) for s in scenes) / len(scenes)
            avg_score = sum(s.get('score', 0) for s in scenes) / len(scenes)
            
            print(f"   Average scene duration: {avg_scene_duration:.1f}s")
            print(f"   Average scene score: {avg_score:.3f}")
            
            motion_scenes = [s for s in scenes if 'motion_score' in s]
            if motion_scenes:
                avg_motion = sum(s['motion_score'] for s in motion_scenes) / len(motion_scenes)
                high_motion_count = len([s for s in motion_scenes if s['motion_score'] > 0.7])
                print(f"   Average motion score: {avg_motion:.3f}")
                print(f"   High-motion scenes (>0.7): {high_motion_count}/{len(motion_scenes)}")
            
        else:
            print("   ❌ No scenes detected!")
            
    except Exception as e:
        print(f"   ❌ Scene detection failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_enhanced_scene_detection()
