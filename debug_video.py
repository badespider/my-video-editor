#!/usr/bin/env python3
"""
Debug script to test video processing pipeline step by step
"""

import os
import sys
sys.path.append('.')

from coordinator import VideoAgent
from utils import get_video_info
from workers import IngestionWorker, ClipChooserWorker

def debug_video_processing():
    video_path = r'C:\Users\dimit\Videos\anime\1mp4.mp4'
    
    print(f"=== Debug Video Processing ===")
    print(f"Video path: {video_path}")
    print(f"Video file exists: {os.path.exists(video_path)}")
    
    if not os.path.exists(video_path):
        print("ERROR: Video file does not exist!")
        return
    
    # Step 1: Get video info
    try:
        print("\n=== Step 1: Getting Video Info ===")
        info = get_video_info(video_path)
        print(f"Video info: {info}")
    except Exception as e:
        print(f"Error getting video info: {e}")
        return
    
    # Step 2: Test Ingestion Worker
    try:
        print("\n=== Step 2: Testing Ingestion Worker ===")
        ingestion_worker = IngestionWorker(state={})
        ingestion_result = ingestion_worker.run(video_path)
        print(f"Ingestion result keys: {list(ingestion_result.keys())}")
        print(f"Number of scenes detected: {len(ingestion_result.get('scenes', []))}")
        if ingestion_result.get('scenes'):
            print(f"First scene: {ingestion_result['scenes'][0]}")
    except Exception as e:
        print(f"Error in ingestion: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test Clip Chooser Worker  
    try:
        print("\n=== Step 3: Testing Clip Chooser Worker ===")
        clip_worker = ClipChooserWorker(state={})
        clips_result = clip_worker.run(ingestion_result)
        print(f"Clips result keys: {list(clips_result.keys())}")
        print(f"Number of clips generated: {len(clips_result.get('clips', []))}")
        if clips_result.get('clips'):
            print(f"First clip: {clips_result['clips'][0]}")
    except Exception as e:
        print(f"Error in clip selection: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Test full pipeline
    try:
        print("\n=== Step 4: Testing Full Pipeline ===")
        agent = VideoAgent()
        result = agent.run_with_video(video_path)
        print(f"Full pipeline completed successfully!")
        print(f"Result keys: {list(result.keys())}")
    except Exception as e:
        print(f"Error in full pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_video_processing()
