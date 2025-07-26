# Updated Workflow with Raw Video Handling

The system will now accept a video file path (e.g., "my_vlog.mp4") instead of just text scripts:

1. **Ingestion/Indexing**: Analyze the video to create a memory layer (e.g., detect scenes with timestamps using MoviePy for frame sampling or mocks).
2. **Story Analysis**: If no script, generate one from video (e.g., transcribe audio or describe visuals).
3. **Choosing Clips**: Select and extract segments (e.g., "Clip from 00:01:45 to 00:03:00" as separate MP4s).
4. **Narration**: Generate and overlay text/audio on clips.
5. **BGM**: Add background music to clips.
6. **Generating/Assembly**: Concatenate extracted clips into one uniform video (e.g., "final_vlog.mp4").

This ensures the agent "understands" the video by breaking it into clips based on analysis, then reassembles them coherently.

---

## Implementation Updates (Python Code Enhancements)

We'll add MoviePy (`pip install moviepy` in real env; mock for REPL). Update the workers to handle video paths. Here's the revised code structure—test each module before integrating.

---

### config.py (Add Video Settings)
```python
# Add to existing config
VIDEO_MAX_DURATION = 600  # Seconds (10 min)
CLIP_MIN_DURATION = 5  # Seconds
```

### utils.py (Add Video Helpers)
```python
from moviepy.editor import VideoFileClip  # For real; mock for now

def extract_clip(video_path, start_time, end_time, output_path):
    # Mock if no moviepy: Create placeholder
    if 'moviepy' not in globals():
        with open(output_path, 'w') as f:
            f.write(f"Mock clip from {start_time} to {end_time}")
        return output_path
    # Real extraction
    clip = VideoFileClip(video_path).subclip(start_time, end_time)
    clip.write_videofile(output_path, codec="libx264")
    return output_path

def assemble_clips(clip_paths, narration_audio=None, bgm_path=None, output_path="final.mp4"):
    # Mock: Create placeholder
    if 'moviepy' not in globals():
        with open(output_path, 'w') as f:
            f.write("Mock assembled video")
        return output_path
    # Real assembly
    from moviepy.editor import concatenate_videoclips, AudioFileClip
    clips = [VideoFileClip(p) for p in clip_paths]
    final = concatenate_videoclips(clips)
    if narration_audio:
        final = final.set_audio(AudioFileClip(narration_audio))
    if bgm_path:
        bgm = AudioFileClip(bgm_path).volumex(0.3)  # Low volume
        final = final.set_audio(final.audio.set_duration(final.duration).overlay(bgm))
    final.write_videofile(output_path)
    return output_path
```

### workers.py (Update for Video)
```python
# Ingestion Worker: Now handles video path
def run(self, video_path: str) -> dict:
    # Mock indexing (real: Use moviepy to get duration/scenes)
    duration = 300  # Mock 5 min
    scenes = [
        {"start": 0, "end": 90, "description": "Intro from video"},
        {"start": 90, "end": 180, "description": "Main action"},
        {"start": 180, "end": 300, "description": "Conclusion"}
    ]
    return {"scenes": scenes, "total_duration": duration, "video_path": video_path}

# Clip Chooser: Extract real clips
def run(self, analysis: dict) -> dict:
    video_path = analysis["video_path"]
    clips = []
    for i, scene in enumerate(analysis["scenes"]):
        start = scene["start"]
        end = scene["end"]
        clip_path = f"clip_{i}.mp4"
        extract_clip(video_path, start, end, clip_path)
        clips.append({"id": i, "path": clip_path, "description": scene["description"], "duration": end - start})
    return {"clips": clips}

# Assembly Worker: Use new assemble_clips
def run(self, clips: dict, narrations: dict, bgms: dict) -> dict:
    clip_paths = [c["path"] for c in clips["clips"]]
    narration_audio = "narration.mp3" if narrations else None  # Mock; expand to TTS
    bgm_path = bgms["bgm_options"][0] if bgms else None
    output_path = assemble_clips(clip_paths, narration_audio, bgm_path)
    return {"final_video": output_path, "plan": "Assembled from clips"}
```

### main.py (Update to Accept Video Path)
```python
# Example run
agent = VideoAgent()
result = agent.run(video_path="my_vlog.mp4")  # Outputs {"final_video": "final.mp4", ...}
```

### Tests (Update for Video)
```python
def test_ingest_video(self):
    # Mock video path
    result = ingest_footage("mock_vlog.mp4")
    self.assertIn("scenes", result)
    self.assertIn("video_path", result)

def test_clip_extraction(self):
    # Mock extract
    path = extract_clip("mock.mp4", 0, 10, "test_clip.mp4")
    self.assertTrue(os.path.exists(path))

def test_assembly(self):
    paths = ["clip1.mp4", "clip2.mp4"]
    output = assemble_clips(paths)
    self.assertEqual(output, "final.mp4")  # Mock check
```
