from workers.workers import ClipChooserWorker, IngestionWorker
import config

print("=== DEBUG CLIP GENERATION ===")

# Test video
video_path = r'C:\Users\dimit\Videos\anime\1mp4.mp4'

# Step 1: Ingestion
print("Step 1: Running Ingestion...")
ingestion_worker = IngestionWorker({})
ingestion_result = ingestion_worker.run(video_path)
print(f"Ingestion result: {ingestion_result['scene_count']} scenes")

# Step 2: Clip selection with detailed logging
print("\nStep 2: Running Clip Selection...")
clip_worker = ClipChooserWorker({})
prompt = "Create multiple clips showcasing different parts of the video"

try:
    clip_result = clip_worker.run(ingestion_result, prompt=prompt)
    clips = clip_result.get('clips', [])
    
    print(f"\n=== CLIP RESULTS ===")
    print(f"Total clips generated: {len(clips)}")
    
    for i, clip in enumerate(clips):
        print(f"\nClip {i+1}:")
        print(f"  Description: {clip.get('description', 'Unknown')}")
        print(f"  Path: {clip.get('path', 'None')}")
        print(f"  Duration: {clip.get('duration', 0):.1f}s")
        print(f"  Score: {clip.get('score', 0):.3f}")
        print(f"  Mood: {clip.get('mood', 'unknown')}")
        
        # Check if file exists
        import os
        clip_path = clip.get('path')
        if clip_path and os.path.exists(clip_path):
            file_size = os.path.getsize(clip_path)
            print(f"  File exists: Yes ({file_size} bytes)")
        else:
            print(f"  File exists: No")

except Exception as e:
    import traceback
    print(f"ERROR: {e}")
    print(f"Traceback: {traceback.format_exc()}")
