# Project Phases and Rules

## Phase 1: Planning and Setup (Days 1-2)

### Rule 1.1: Real Detection Integration
- **Requirement**: Fully activate PySceneDetect and OpenCV in detection functions for precise scene/motion analysis.

**Implementation Steps:**
- Update `_detect_scenes_real` to include `min_scene_len` and adaptive thresholds.
- Integrate motion params in `calculate_motion_score` (e.g., `varThreshold` for MOG2).

**Code Example (utils.py):**
```python
from scenedetect import detect, ContentDetector
import cv2

def _detect_scenes_real(path):
    detector = ContentDetector(threshold=config.SCENE_DETECTION_THRESHOLD, min_scene_len=config.MIN_SCENE_DURATION * 30)  # FPS assumption
    scene_list = detect(path, detector)
    scenes = [{"start": s[0].get_seconds(), "end": s[1].get_seconds(), "description": "Detected scene"} for s in scene_list]
    for s in scenes:
        s["motion_score"] = calculate_motion_score(path, s["start"], s["end"])
    return scenes
```

**Testing:**
- Assert scenes meet `min_duration`; `motion_scores` vary realistically (e.g., >0.7 for high-motion).
- Unittest with mock videos; integration with real 5min clip.

**Mitigation:**
- Toggle `USE_REAL_DETECTION=False` for mocks; log if libs missing.

### Rule 1.2: Prompt and Editing Refinement Preparation
- **Requirement**: Enhance prompt parsing to prevent hallucinations and support complex edits.

**Implementation Steps:**
- Add validation to `_parse_edit_prompt` (e.g., check trim >0).
- Prep for effects like fades in new `_apply_effects` method.

**Code Example (workers.py):**
```python
def _parse_edit_prompt(self, prompt):
    response = call_model(f"Parse editing params from: {prompt}. Return JSON only.", task_type="parse")
    params = json.loads(response).get("params", {})
    # Validate
    if 'trim' in params and (not isinstance(params['trim'], int) or params['trim'] <= 0):
        params['trim'] = config.MAX_CLIP_DURATION  # Fallback
    return params
```

**Testing:**
- Assert invalid "trim:abc" falls back; 100% valid params in 10 prompts.
- Unittest AI/rule paths.

**Mitigation:**
- Strict prompts to avoid hallucinations; rule-based if AI fails.

### Rule 1.3: Performance Optimization Setup
- **Requirement**: Prepare auto-chunking and FFmpeg for better scalability.

**Implementation Steps:**
- Add FFmpeg subprocess in `extract_clip` for optional fast extraction.
- Enable auto-chunk in `motion_score`.

**Code Example (utils.py):**
```python
import subprocess

def extract_clip(video_path, start, end, output_path, use_ffmpeg=False):
    if use_ffmpeg:
        cmd = ['ffmpeg', '-i', video_path, '-ss', str(start), '-to', str(end), '-c:v', 'libx264', '-c:a', 'aac', output_path]
        subprocess.run(cmd, check=True)
        return output_path
    # MoviePy fallback...
```

**Testing:**
- Benchmark FFmpeg vs MoviePy (expect 2x faster); assert no audio loss.
- Stress test with 30min video.

**Mitigation:**
- Config `ENABLE_FFMPEG=False` if not installed; log subprocess errors.

### Rule 1.4: Testing and Docs Expansion Preparation
- **Requirement**: Plan updates for legacy tests and new guides.

**Implementation Steps:**
- Identify outdated tests (e.g., lines 73-74); prepare "Prompt Guide" in README.

**Testing:**
- Coverage report >95% post-updates.
- Manual review of new docs.

**Mitigation:**
- Incremental updates to avoid breaking CI.

## Phase 2: Core Implementation (Days 3-4)

### Rule 2.1: Activate Real Detection
- **Requirement**: Complete PySceneDetect/OpenCV integration for accurate analysis.

**Implementation Steps:**
- Add `min_scene_len` to `ContentDetector`; tune MOG2 params in motion.

**Code Example (utils.py - Motion Update):**
```python
def calculate_motion_score(video_path, start, end):
    # ... existing
    bg_subtractor = cv2.createBackgroundSubtractorMOG2(varThreshold=config.MOTION_DIFF_THRESHOLD)
    # Process frames...
```

**Testing:**
- Assert motion >0.7 for action clips; integration with `IngestionWorker`.
- Metric: Precision >90% vs manual scenes.

**Mitigation:**
- Default params if config invalid.

### Rule 2.2: Refine Prompts and Editing
- **Requirement**: Improve parsing and add effects implementation.

**Implementation Steps:**
- Implement `_apply_effects` with MoviePy fx (e.g., fadein).

**Code Example (workers.py):**
```python
from moviepy.video.fx.all import fadein

def _apply_effects(self, clip_path, effect="fade"):
    clip = VideoFileClip(clip_path).fx(fadein, 2)  # 2s fade, keep audio
    clip.write_videofile(clip_path)  # Overwrite or new path
```

**Testing:**
- Assert fade applied (manual check or duration unchanged); no audio change.
- Prompt test: "add fades" triggers effect.

**Mitigation:**
- Skip if effect unsupported; log.

## Phase 3: Optimization and Integration (Days 5-6)

### Rule 3.1: Implement Performance Boosts
- **Requirement**: Auto-chunk in motion and use FFmpeg for extraction.

**Implementation Steps:**
- Call `chunk_video` in `calculate_motion_score` if duration > threshold.

**Code Example (utils.py):**
```python
def calculate_motion_score(video_path, start, end):
    duration = end - start
    if duration > config.VIDEO_CHUNK_SIZE:
        chunks = chunk_video(video_path, config.VIDEO_CHUNK_SIZE)
        scores = [calculate_motion_score(chunk, 0, len(chunk)) for chunk in chunks]  # Adjust times
        return sum(scores) / len(scores)
    # Normal calculation...
```

**Testing:**
- Assert scores consistent; time <30s for 10min segment.
- Load test: No OOM on large files.

**Mitigation:**
- Fallback to mock score=0.5 if chunk fails.

### Rule 3.2: Integrate and Test
- **Requirement**: Ensure workflow uses new features; validate coverage.

**Implementation Steps:**
- Update `run_with_video` to pass prompts; call cleanup.

**Testing:**
- End-to-end: Prompt "focus:action, trim:30" yields edited clips with audio.
- Coverage >95%; no failures in phase tests.

**Mitigation:**
- Log low coverage; retry.

## Phase 4: Expansion (Days 7-8)

### Rule 4.1: Expand Tests and Docs
- **Requirement**: Update legacy tests; add guides.

**Implementation Steps:**
- Rewrite `test_ultimate_coverage.py` for new lines; add "Editing Guide" to README with examples.

**Testing:**
- All tests pass; docs reviewed for accuracy.

**Mitigation:**
- CI gates for coverage.

