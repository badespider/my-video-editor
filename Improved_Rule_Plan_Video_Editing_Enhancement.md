# Improved Rule Plan for Video Editing Enhancement

This enhanced rule plan builds on the original by adding more detailed sub-steps, expanded code examples (with full functions where relevant), specific testing metrics (e.g., coverage percentages, assertions), additional mitigations (e.g., config toggles, logging), and sub-rules for clarity. It maintains focus on clip editing/assembly improvements, preserves original audio, holds narration/BGM (via config), and ensures modularity for Memories.ai integration. Phases are extended with timelines and dependencies. **Total: ~10 days, iterable.**

## Phase 1: Planning and Setup (Days 1-2)
**Goal:** Define scope, update config for new features, and prepare for prompt-based editing.

### Rule 1.1: Advanced Clip Intelligence
Enhance ClipChooser to use content scores for prioritization and support user prompts for custom edits (e.g., "focus on action scenes" filters high-motion clips).

#### Sub-Rules:
- **1.1.1:** Scores must include motion (from scene analysis) and user relevance (from prompt match).
- **1.1.2:** Prompts parsed via call_model to extract params (e.g., "trim:30s, focus:action" → duration=30, mood="intense").

#### Implementation Steps:
1. Add prompt param to ClipChooser run.
2. Parse prompt in new `_parse_edit_prompt` method.
3. Filter/sort scenes based on parsed params and scores.

#### Code Example (workers.py - Full run method update):
```python
def run(self, analysis, prompt=None):
    scenes = analysis["scenes"]
    if prompt:
        params = self._parse_edit_prompt(prompt)  # E.g., {"focus": "action", "trim": 30}
        filtered = [s for s in scenes if s["mood"] == params.get("focus", "neutral")] if "focus" in params else scenes
        scenes = filtered
    selected = self._select_diverse_scenes(scenes, analysis["total_duration"])
    clips = []
    for i, scene in enumerate(selected):
        start = scene["start"]
        end = min(start + params.get("trim", config.MAX_CLIP_DURATION), scene["end"])
        clip_path = f"clip_{i}.mp4"
        extract_clip(analysis["video_path"], start, end, clip_path)  # Preserves audio
        clips.append({
            "id": i, 
            "path": clip_path, 
            "description": scene["description"], 
            "duration": end - start, 
            "mood": scene["mood"]
        })
    return {"clips": clips}

def _parse_edit_prompt(self, prompt):
    response = call_model(f"Parse editing params from: {prompt}", task_type="parse")
    return json.loads(response).get("params", {})  # E.g., {"focus": "action", "trim": 30}
```

#### Testing:
- Assert prompt "focus:action" returns only "intense" moods (len(filtered) == expected).
- **Metric:** 100% match rate in 5 test prompts.
- **Unittest:** Mock call_model; verify params dict.
- **Mitigation:** If prompt invalid, log and fallback to auto-selection; config PROMPT_REQUIRED = False.

### Rule 1.2: Performance Optimization
Implement chunking to limit long videos (process in segments) and parallel extraction for speed.

#### Sub-Rules:
- **1.2.1:** Chunk size max 300s; auto-chunk if > VIDEO_MAX_DURATION.
- **1.2.2:** Parallel limit to MAX_CONCURRENT_WORKERS (4 default).

#### Implementation Steps:
1. Add chunk_video in utils.py; call in Ingestion if duration > limit.
2. Use Pool in ClipChooser for extraction.

#### Code Example (utils.py - New functions):
```python
def chunk_video(video_path, chunk_dur=config.VIDEO_MAX_DURATION / 2):
    clip = VideoFileClip(video_path)
    duration = clip.duration
    chunks = []
    for start in range(0, int(duration), chunk_dur):
        end = min(start + chunk_dur, duration)
        chunk_path = f"chunk_{start}.mp4"
        clip.subclipped(start, end).write_videofile(chunk_path)  # Preserve audio
        chunks.append(chunk_path)
    return chunks

# In ClipChooser:
from multiprocessing import Pool

def _extract_parallel(self, args_list):
    with Pool(config.MAX_CONCURRENT_WORKERS) as p:
        p.map(extract_clip, args_list)  # Parallel calls
```

#### Testing:
- **Benchmark:** 10min video processes in <1min (sequential vs parallel).
- Assert no timeouts (e.g., time < WORKER_TIMEOUT).
- **Unittest:** Mock chunks; verify full duration covered.
- **Mitigation:** Fallback to sequential if Pool fails (e.g., low RAM); log chunk stats.

## Phase 2: Implementation (Days 3-5)

### Rule 2.1: Enhanced Detection
Integrate real PySceneDetect for better scene analysis when enabled.

#### Sub-Rules:
- **2.1.1:** Threshold adjustable via config for sensitivity.
- **2.1.2:** Combine with motion analysis (e.g., OpenCV in _detect_scenes_real for score boost).

#### Implementation Steps:
1. Update detect_scenes to use ContentDetector; add motion scoring.

#### Code Example (utils.py):
```python
from scenedetect import detect, ContentDetector
import cv2  # For motion

def _detect_scenes_real(path):
    scene_list = detect(path, ContentDetector(threshold=config.SCENE_DETECTION_THRESHOLD))
    scenes = [{"start": s[0].get_seconds(), "end": s[1].get_seconds(), "description": "Detected scene"} for s in scene_list]
    for s in scenes:
        s["motion_score"] = _calculate_motion(path, s["start"], s["end"])  # Custom motion func
    return scenes

def _calculate_motion(video_path, start, end):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    prev_frame = None
    motion = 0
    while cap.get(cv2.CAP_PROP_POS_MSEC) < end * 1000:
        ret, frame = cap.read()
        if not ret: break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is not None:
            diff = cv2.absdiff(gray, prev_frame)
            motion += cv2.countNonZero(diff)
        prev_frame = gray
    cap.release()
    return motion / ((end - start) * 30)  # Normalize per frame
```

#### Testing:
- Assert scenes have motion_scores >0; coverage 100%.
- **Local video test:** Compare real vs mock outputs.
- **Mitigation:** If OpenCV missing, default motion_score=0.5; log.

### Rule 2.2: Editing Operations
Implement trim/reorder in assembly based on scores or prompt.

#### Sub-Rules:
- **2.2.1:** Trim to config.CLIP_MIN_DURATION if low score.
- **2.2.2:** Reorder by "intensity" (motion score) if prompted.

#### Implementation Steps:
1. Add `_trim_clips` and `_reorder_clips` in AssemblyWorker.

#### Code Example (workers.py):
```python
def run(self, clips, prompt=None):
    if prompt and "trim" in prompt:
        clips["clips"] = [self._trim_clip(c, duration=60) for c in clips["clips"]]  # Example trim
    sorted_clips = self._reorder_clips(clips["clips"], order="score")
    clip_paths = [c["path"] for c in sorted_clips]
    return assemble_clips(clip_paths)

def _trim_clip(self, clip, duration):
    return VideoFileClip(clip["path"]).subclipped(0, duration)  # Trim, keep audio

def _reorder_clips(self, clips, order="score"):
    if order == "score":
        return sorted(clips, key=lambda c: c["score"], reverse=True)
    return clips
```

#### Testing:
- Assert trimmed duration =60s; reordered by descending score.
- **Metric:** 100% audio preservation (compare input/output audio lengths).
- **Mitigation:** Optional flags; fallback to no edit if error.

## Phase 3: Integration/Testing (Days 6-7)

### Rule 3.1: Workflow Integration
Coordinator passes editing prompts to assembly from run_with_video.

#### Implementation Steps: 
1. Add edit_prompt param.

#### Code Example (coordinator.py):
```python
def run_with_video(self, path, edit_prompt=None):
    ingestion = IngestionWorker().run(path)
    clips = ClipChooserWorker().run(ingestion)
    assembly = AssemblyWorker().run(clips, prompt=edit_prompt)
    return assembly
```

#### Testing:
- **End-to-end:** "trim to 30s" results in shorter clips.
- Assert coverage >80% post-edits.
- **Mitigation:** Log if prompt invalid.

### Rule 3.2: Cleanup
Expand to delete edited temps.

#### Implementation Steps: 
1. Add .mp4 to mock_files in cleanup_mocks.

#### Testing: 
- Assert no files left.
- **Mitigation:** Auto in prod.

## Phase 4: Expansion (Days 8+)

### Rule 4.1: Model Switch
Test Grok-4 for editing prompts (e.g., "trim action scenes").

#### Implementation Steps: 
1. Update config; test.

#### Testing: 
- Assert parsed params accurate.
- **Mitigation:** Rule-based fallback.

### Rule 4.2: Memories.ai Integration
Prepare integration hooks for advanced video understanding.

#### Sub-Rules:
- **4.2.1:** Add placeholder API calls for scene understanding.
- **4.2.2:** Implement fallback to local analysis if API unavailable.

#### Implementation Steps:
1. Add Memories.ai API configuration in config.py
2. Create integration wrapper in utils.py
3. Update scene detection to use Memories.ai when available

#### Code Example (utils.py):
```python
def detect_scenes_memories_ai(video_path):
    """Use Memories.ai API for advanced scene detection"""
    if not config.MEMORIES_AI_API_KEY:
        logging.warning("Memories.ai API key not found, falling back to local detection")
        return _detect_scenes_mock(video_path)
    
    try:
        # Placeholder for Memories.ai API integration
        response = call_memories_ai_api(video_path, "scene_detection")
        return parse_memories_ai_scenes(response)
    except Exception as e:
        logging.error(f"Memories.ai API failed: {e}, falling back to local detection")
        return _detect_scenes_mock(video_path)

def call_memories_ai_api(video_path, task_type):
    """Placeholder for actual Memories.ai API calls"""
    # This would implement the actual API integration
    # For now, return mock data
    return {"scenes": [], "status": "mock"}
```

#### Testing:
- Assert API integration doesn't break existing workflow
- **Metric:** 100% fallback coverage when API unavailable
- **Mitigation:** Always provide local fallback; log API status

## Configuration Updates

### Enhanced Config Options:
```python
# Advanced editing features
ENABLE_PROMPT_EDITING = True
PROMPT_REQUIRED = False
MAX_CONCURRENT_WORKERS = 4
SCENE_DETECTION_THRESHOLD = 30.0

# Performance optimization
VIDEO_CHUNK_SIZE = 300  # seconds
ENABLE_PARALLEL_PROCESSING = True
WORKER_TIMEOUT = 120  # seconds

# Memories.ai integration
MEMORIES_AI_API_KEY = os.getenv("MEMORIES_AI_API_KEY", "")
MEMORIES_AI_ENDPOINT = "https://api.memories.ai/v1"
ENABLE_MEMORIES_AI = True

# Motion analysis
ENABLE_MOTION_DETECTION = True
MOTION_THRESHOLD = 0.3

# Audio preservation
PRESERVE_ORIGINAL_AUDIO = True
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "128k"
```

## Testing Strategy

### Unit Tests:
- **Coverage target:** >90% for new functions
- **Test categories:** Prompt parsing, scene filtering, audio preservation, parallel processing
- **Mock strategy:** Mock external APIs (Memories.ai, OpenAI) and file operations

### Integration Tests:
- **End-to-end workflows:** Complete video processing with various prompts
- **Performance benchmarks:** Processing time comparisons (sequential vs parallel)
- **Error handling:** API failures, invalid prompts, corrupted videos

### Acceptance Criteria:
1. **Functionality:** All prompt-based editing works as specified
2. **Performance:** 50% improvement in processing time for videos >5min
3. **Quality:** Audio preservation in 100% of processed clips
4. **Reliability:** <5% failure rate in production scenarios
5. **Maintainability:** Clean separation of concerns, proper error handling

## Risk Mitigation

### Technical Risks:
- **Memory issues with large videos:** Implement chunking and streaming
- **API rate limits:** Implement exponential backoff and caching
- **Audio/video sync issues:** Validate timestamps throughout pipeline

### Operational Risks:
- **Config changes breaking existing workflows:** Maintain backward compatibility
- **Performance degradation:** Continuous benchmarking and optimization
- **Integration complexity:** Modular design with clear interfaces

## Timeline and Dependencies

### Critical Path:
1. **Days 1-2:** Config updates and prompt parsing (blocking for Phase 2)
2. **Days 3-4:** Scene detection and motion analysis (parallel with editing ops)
3. **Days 5-6:** Assembly operations and workflow integration
4. **Days 7-8:** Testing and performance optimization
5. **Days 9-10:** Memories.ai integration and documentation

### Parallel Tracks:
- **Testing:** Can start on Day 3 with unit tests for completed components
- **Documentation:** Continuous throughout development
- **Performance monitoring:** Implement early for baseline measurements

This enhanced rule plan provides a comprehensive roadmap for video editing improvements while maintaining system stability and preparing for future AI integrations.
