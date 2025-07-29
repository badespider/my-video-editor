from workers.workers import ClipChooserWorker, IngestionWorker
import config

print("=== SIMPLE CLIP GENERATION TEST ===")

# Test video
video_path = r'C:\Users\dimit\Videos\anime\1mp4.mp4'

# Step 1: Ingestion
print("Step 1: Running Ingestion...")
ingestion_worker = IngestionWorker({})
ingestion_result = ingestion_worker.run(video_path)
scenes = ingestion_result['scenes']
print(f"Ingestion result: {len(scenes)} scenes")

# Show scene details
for i, scene in enumerate(scenes):
    score = scene.get('score', 0)
    passes = score >= config.SCENE_SCORE_THRESHOLD
    print(f"  Scene {i+1}: {scene['start']:.1f}s-{scene['end']:.1f}s (score: {score:.3f}) {'✅' if passes else '❌'}")

# Step 2: Simple clip selection without prompt (just pass None)
print(f"\nStep 2: Running Clip Selection without prompt...")
clip_worker = ClipChooserWorker({})

try:
    # Pass None for prompt to avoid prompt parsing issues
    clip_result = clip_worker.run(ingestion_result, prompt=None)
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
