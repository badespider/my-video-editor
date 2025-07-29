from workers.workers import ClipChooserWorker
from utils import get_video_info, detect_scenes
import os

print('=== FINAL END-TO-END TEST ===')

# Test with your anime video
video_path = r'C:\Users\dimit\Videos\anime\1mp4.mp4'
print(f'Testing with video: {video_path}')

# Check if video exists
if not os.path.exists(video_path):
    print(f'Video not found: {video_path}')
    exit(1)

# Get video info
try:
    video_info = get_video_info(video_path)
    print(f'Video duration: {video_info.get("duration", 0)}s')
except Exception as e:
    print(f'Failed to get video info: {e}')
    exit(1)

# Detect scenes
try:
    scenes = detect_scenes(video_path)
    print(f'Scenes detected: {len(scenes)}')
    for i, scene in enumerate(scenes):
        print(f'  Scene {i+1}: {scene["start"]:.1f}s-{scene["end"]:.1f}s (score: {scene.get("score", 0):.3f})')
except Exception as e:
    print(f'Scene detection failed: {e}')
    exit(1)

# Test ClipChooserWorker
try:
    worker = ClipChooserWorker({})
    analysis = {
        'scenes': scenes,
        'video_path': video_path,
        'total_duration': video_info.get('duration', 300)
    }
    
    result = worker.run(analysis)
    clips = result.get('clips', [])
    
    print(f'\n=== CLIP SELECTION RESULTS ===')
    print(f'Clips generated: {len(clips)}')
    
    for i, clip in enumerate(clips):
        print(f'  Clip {i+1}: {clip.get("description", "Unknown")}')
        print(f'    Path: {clip.get("path", "None")}')
        print(f'    Duration: {clip.get("duration", 0):.1f}s')
        print(f'    Score: {clip.get("score", 0):.3f}')
        print(f'    Mood: {clip.get("mood", "unknown")}')
        
        # Check if file actually exists
        clip_path = clip.get('path')
        if clip_path and os.path.exists(clip_path):
            file_size = os.path.getsize(clip_path)
            print(f'    File exists: Yes ({file_size} bytes)')
        else:
            print(f'    File exists: No')
        print()
    
    print('SUCCESS: ClipChooserWorker completed without errors!')
    
except Exception as e:
    import traceback
    print(f'ClipChooserWorker failed: {e}')
    print(f'Traceback: {traceback.format_exc()}')
