#!/usr/bin/env python3
"""
Test enhanced narration with a real video file
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from coordinator import VideoAgent
import json

def test_narration_with_real_video():
    """Test enhanced narration with the anime video"""
    
    video_path = r"C:\Users\dimit\Videos\anime\1mp4.mp4"
    
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return
    
    print("=== Testing Enhanced Narration with Real Video ===\n")
    print(f"Video: {video_path}")
    
    # Create a test script for narration testing
    test_script = """
    A young anime warrior discovers an ancient temple hidden in the mountains. 
    Inside, magical crystals pulse with mysterious energy while ancient guardians 
    awaken to protect their sacred treasures. The hero must prove their worth 
    through combat and wisdom to claim the legendary artifact within.
    """
    
    # Initialize the coordinator
    coordinator = VideoAgent()
    
    print("Processing video with enhanced narration system...")
    
    try:
        # Run the video analysis pipeline
        result = coordinator.run_with_video(video_path)
        
        print("\n=== Narration Results ===")
        
        # Look for narration in the result
        if 'narration' in result:
            narration_data = result['narration']
            print(f"Narration Text: {narration_data.get('narration', 'Not found')}")
            print(f"Audio Path: {narration_data.get('audio_path', 'Not found')}")
            print(f"Word Count: {narration_data.get('word_count', 0)}")
            print(f"Segment Count: {narration_data.get('segment_count', 0)}")
        
        # Look at the clips that were generated
        if 'clips' in result:
            clips = result['clips']
            print(f"\n=== Generated Clips ({len(clips)}) ===")
            for i, clip in enumerate(clips, 1):
                print(f"Clip {i}: {clip.get('description', 'No description')[:100]}...")
        
        print(f"\n=== Final Video ===")
        if 'final_video' in result:
            print(f"Final Video Path: {result['final_video']}")
        
        # Check if narration audio file was created
        anime_folder = r"C:\Users\dimit\Videos\anime"
        narration_files = [f for f in os.listdir(anime_folder) if 'narration' in f.lower()]
        
        if narration_files:
            print(f"\nNarration Audio Files Created:")
            for nf in narration_files:
                file_path = os.path.join(anime_folder, nf)
                file_size = os.path.getsize(file_path)
                print(f"  - {nf} ({file_size} bytes)")
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Enhanced Narration Real Video Test Complete ===")

if __name__ == "__main__":
    test_narration_with_real_video()
