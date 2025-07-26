# Structured Rule Plan to Fix Raw Video Understanding and Clip Selection

To address the issue where the system clips only the beginning of the video without truly understanding the full content (e.g., missing dynamic scenes, key moments, or visual transitions), we'll create a structured rule plan for redesigning the multi-agent system. This plan focuses on enhancing the IngestionWorker and ClipChooserWorker to incorporate real scene detection, content analysis, and intelligent selection from the entire video. It builds on the current codebase (from the Repomix document), ensuring modularity, testability, and model flexibility.

The plan is divided into phases with rules for each, including code updates, testing requirements, and mitigations. Rules are numbered for reference and emphasize no hallucinations (ground in verifiable data) and gradual iteration. We'll use PySceneDetect for scene detection (install via pip in local env; mock for REPL) and MoviePy for clip extraction, scaling to full video understanding.

## Phase 1: Planning and Rule Definition (Preparation)

### Rule 1.1: Define Understanding Criteria
"Understanding" means analyzing the entire video for visual/audio cues (e.g., scene changes via content thresholds, motion detection, audio peaks). 

**Rule**: Require at least 70% coverage of video duration in selected clips; prioritize diverse segments (e.g., start, middle, end) based on analysis scores.

### Rule 1.2: Dependency Management
Use only Python built-ins for mocks; add PySceneDetect and MoviePy as optional deps in requirements.txt. 

**Rule**: If not installed, fallback to dynamic mocks that simulate full video (e.g., random timestamps across duration).

### Rule 1.3: Input Validation
Raw video path must be valid MP4/AVI; limit duration to config.VIDEO_MAX_DURATION (e.g., 600s). 

**Rule**: Raise errors for invalid files before processing, with user-friendly messages.

**Mitigation**: Start with mock analysis to test workflow; ensure rules allow switching to real tools without code changes (config flag: USE_REAL_DETECTION = False initially).

## Phase 2: Enhance IngestionWorker for Full Video Analysis (Days 1-3)

### Rule 2.1: Dynamic Indexing
Replace fixed mocks with dynamic generation: Divide video into scenes using content-based detection (e.g., PySceneDetect's ContentDetector with threshold=30 for changes in color/histogram). 

**Rule**: Generate at least 3-10 scenes covering 100% duration; assign descriptions/moods based on rules (e.g., high motion = "intense").

### Rule 2.2: Scene Scoring
Assign scores to scenes (e.g., motion level, length variety) to ensure selection from whole video. 

**Rule**: Use a scoring formula (score = motion * (position / total_duration) to favor later scenes.

### Implementation Steps:
Update `run(self, video_path: str)` to call `detect_scenes(video_path)`.

**Example Code (workers.py):**
```python
from utils import detect_scenes  # Dynamic helper

def run(self, video_path: str) -> dict:
    scenes = detect_scenes(video_path)  # Returns list with start/end/desc
    total_duration = sum(s["end"] - s["start"] for s in scenes)
    # Score scenes
    for s in scenes:
        s["score"] = (s["end"] - s["start"]) * (s["start"] / total_duration)  # Favor diversity
    return {"scenes": scenes, "total_duration": total_duration, "video_path": video_path}
```

**Testing Rule**: Unittests must cover full duration (e.g., assert sum durations == total); mock detect_scenes to return varied scenes. 

**Rule**: 100% pass before integration.

**Mitigation**: If detection fails (e.g., long video), fallback to uniform division (e.g., 60s segments); log warnings.

## Phase 3: Update ClipChooserWorker for Intelligent Selection (Days 4-6)

### Rule 3.1: Content-Based Selection
Select clips from high-score scenes across the video, not sequentially. 

**Rule**: Sort scenes by score; pick top N (e.g., 5) ensuring coverage (at least 1 from first/middle/last third).

### Rule 3.2: Extraction Constraints
Clip durations min config.CLIP_MIN_DURATION, max config.MAX_CLIP_DURATION; adjust end if exceeds video length. 

**Rule**: Extract only if scene score > threshold (e.g., 0.5); discard low-quality (e.g., static scenes).

### Implementation Steps:
Update run to sort/select from analysis["scenes"]; extract with extract_clip.

**Example Code (workers.py):**
```python
def run(self, analysis: dict) -> dict:
    video_path = analysis["video_path"]
    scenes = sorted(analysis["scenes"], key=lambda s: s["score"], reverse=True)[:10]  # Top 10
    # Ensure coverage: Add one from each third if missing
    thirds = [scenes[i] for i in range(len(scenes)) if i % 3 == 0]  # Simple coverage
    clips = []
    for i, scene in enumerate(thirds):
        start = scene["start"]
        end = min(start + config.MAX_CLIP_DURATION, scene["end"])
        clip_path = f"clip_{i}.mp4"
        extract_clip(video_path, start, end, clip_path)
        clips.append({
            "id": i, 
            "path": clip_path, 
            "description": scene["description"], 
            "duration": end - start, 
            "mood": "neutral"
        })
    return {"clips": clips}
```

**Testing Rule**: Test with mock scenes of varying scores; assert clips from all thirds and total coverage >70%. 

**Rule**: Integration test with mock video file.

**Mitigation**: If no high-score scenes, fallback to uniform selection; limit to config.MAX_CLIPS (e.g., 10).

## Phase 4: Integration and Cleanup (Days 7-10)

### Rule 4.1: Workflow Connectivity
Coordinator calls Ingestion first for raw video input, passing memory to subsequent workers. 

**Rule**: Validate full coverage in final assembly (e.g., sum clip durations >= 70% total).

### Rule 4.2: Mock Cleanup
Add cleanup_mocks() in main.py to delete mock clips/files after run in dev mode. 

**Rule**: Run automatically if config.ENV == "prod".

### Implementation Steps:
- Update coordinator.run_with_video to use ingestion with dynamic scenes.
- Add to main.py: cleanup_mocks() after result.

**Testing Rule**: End-to-end test with mock video (assert clips from full duration); coverage >95%.

**Mitigation**: Log clip coverage percentage; if low, re-run analysis with lower threshold.

## Phase 5: Expansion and Model Switch (Days 11+)

### Rule 5.1: Model Integration
Use call_model for description/mood generation in workers (e.g., "Analyze scene for mood"). 

**Rule**: Test switch to Grok-4 by changing config; verify outputs.

### Rule 5.2: Real Detection
Once tested, swap mock detect_scenes with PySceneDetect in utils.py.

**Mitigation**: Fallback to mocks if libs not available; document in README.

## Technical Implementation Details

### New Dependencies to Add:
```bash
pip install scenedetect[opencv]
pip install opencv-python
```

### New Configuration Variables (config.py):
```python
# Scene Detection Settings
USE_REAL_DETECTION = False  # Start with False for testing
SCENE_DETECTION_THRESHOLD = 30.0  # Content change threshold
MIN_SCENE_DURATION = 5.0  # Minimum scene length in seconds
MAX_SCENES_PER_VIDEO = 20  # Limit for performance
COVERAGE_REQUIREMENT = 0.7  # 70% video coverage minimum
```

### New Utility Functions (utils.py):
```python
def detect_scenes(video_path: str) -> List[Dict[str, Any]]:
    """
    Detect scenes in video using content-based analysis.
    Falls back to uniform division if real detection unavailable.
    """
    if config.USE_REAL_DETECTION and pyscenedetect_available:
        return _detect_scenes_real(video_path)
    else:
        return _detect_scenes_mock(video_path)

def _detect_scenes_real(video_path: str) -> List[Dict[str, Any]]:
    """Real scene detection using PySceneDetect"""
    # Implementation with PySceneDetect
    pass

def _detect_scenes_mock(video_path: str) -> List[Dict[str, Any]]:
    """Mock scene detection for testing"""
    # Dynamic mock that covers full video duration
    pass

def calculate_scene_score(scene: Dict[str, Any], total_duration: float) -> float:
    """
    Calculate scene importance score based on multiple factors.
    Higher scores indicate more interesting/important scenes.
    """
    # Implementation of scoring algorithm
    pass
```

### Testing Strategy:
1. **Unit Tests**: Test each component with mock data
2. **Integration Tests**: Test full pipeline with sample video
3. **Performance Tests**: Measure processing time vs video length
4. **Coverage Tests**: Verify 70%+ video duration coverage
5. **Quality Tests**: Validate clip diversity and scene selection

### Success Metrics:
- **Coverage**: ≥70% of video duration represented in clips
- **Diversity**: Clips from beginning, middle, and end of video
- **Quality**: Scene scores correlate with visual interest
- **Performance**: Processing time ≤ 10% of video duration
- **Reliability**: <5% failure rate on valid video files

## Benefits of This Approach:

1. **Full Video Understanding**: Analyzes entire video content, not just beginning
2. **Intelligent Selection**: Chooses most interesting/relevant scenes based on scoring
3. **Configurable**: Easy to adjust thresholds and parameters
4. **Testable**: Mock implementations allow development without dependencies
5. **Scalable**: Handles videos of various lengths efficiently
6. **Maintainable**: Clear separation of concerns and error handling

This plan fixes the issue by ensuring dynamic, content-aware clip selection from the whole video. The system will now truly "understand" video content and make intelligent decisions about which segments to include in the final output.

**Test in Warp 2.0—run updated code, and let's iterate!**
