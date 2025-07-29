# Rule Development Plan for Suggestions for Improvement

This rule-based development plan implements the suggested improvements to the multi-agent AI video editor codebase, focusing on real detection enhancements, prompt/editing refinement, performance optimization, and testing/docs expansion. It reserves a placeholder for Memories.ai API integration (as a future expansion rule), but currently relies on GPT and other AI models (e.g., Grok-4, OpenAI) for analysis. The plan is structured in 5 phases over 10 days, with TDD emphasis, modularity, and no hallucinations (outputs grounded in data). Rules ensure backward compatibility and scalability.

---

## Phase 1: Planning and Setup (Days 1-2)

### Rule 1.1: Prepare Real Detection Enhancements
**Requirement**: Tune PySceneDetect and OpenCV for accurate scene/motion analysis across full videos.

**Implementation Steps**: 
- Update config with new params (e.g., ADAPTIVE_MIN_SCENE_LEN=True).
- Add Memories.ai placeholder in detect_scenes (call_model with GPT for now, swap to API later).

**Code Example** (utils.py - Placeholder Update):
```python
def detect_scenes(video_path: str) -> List[Dict[str, Any]]:
    if config.ENABLE_MEMORIES_AI and memories_available:  # Future flag
        return detect_scenes_memories_ai(video_path)  # Real API when available
    else:
        # Use GPT for mock description generation now
        response = call_model(f"Analyze video scenes from {video_path}", model="gpt-4")
        scenes = json.loads(response).get("scenes", [])
        for s in scenes:
            s["motion_score"] = calculate_motion_score(video_path, s["start"], s["end"])
        return scenes
```

**Testing**: 
- Assert scenes have adaptive lengths (e.g., >15s min); mock GPT response.
- Unittest placeholder (returns GPT-mocked scenes).

**Mitigation**: 
- Fallback to uniform mocks if GPT fails; log "Memories.ai not available, using GPT".

### Rule 1.2: Prompt and Editing Refinement Setup
**Requirement**: Validate prompts strictly and prepare effects implementation.

**Implementation Steps**: 
- Enhance _parse_edit_prompt with type checks (e.g., trim as int).
- Add _apply_effects skeleton (use GPT for description, MoviePy for real).

**Code Example** (workers.py):
```python
def _parse_edit_prompt(self, prompt):
    response = call_model(f"Parse params from: {prompt}. JSON only.", model="gpt-4")
    params = json.loads(response).get("params", {})
    # Strict validation
    if 'trim' in params:
        try:
            params['trim'] = int(params['trim'])
            if params['trim'] <= 0:
                raise ValueError
        except:
            params['trim'] = config.MAX_CLIP_DURATION
    return params
```

**Testing**: 
- Assert invalid trim defaults; 100% valid in tests with GPT mocks.
- Unittest effects prep (no-op for now).

**Mitigation**: 
- Rule-based if GPT hallucinates (e.g., regex fallback); log invalid params.

### Rule 1.3: Performance Optimization Preparation
**Requirement**: Setup auto-chunking and FFmpeg integration.

**Implementation Steps**: 
- Add FFmpeg toggle in config; implement in extract_clip.
- Prepare motion_score for chunking.

**Code Example** (utils.py):
```python
def calculate_motion_score(video_path, start, end):
    if end - start > config.VIDEO_CHUNK_SIZE:
        chunks = chunk_video(video_path)
        scores = [calculate_motion_score(c, 0, len(c)) for c in chunks]
        return sum(scores) / len(scores)
    # Normal OpenCV calculation...
```

**Testing**: 
- Benchmark chunking (time < previous); assert average scores.
- Unittest FFmpeg path (mock subprocess).

**Mitigation**: 
- Disable FFmpeg if not found; limit chunks to avoid OOM.

### Rule 1.4: Testing and Docs Expansion Setup
**Requirement**: Identify legacy tests and draft new guides.

**Implementation Steps**: 
- List outdated tests; add "Prompt Guide" section in README draft.
- Prep Memories.ai docs placeholder.

**Testing**: 
- Coverage baseline >95%.
- Manual doc review.

**Mitigation**: 
- Phase-gated updates to prevent CI breaks.

---

## Phase 2: Implementation - Detection & Prompts (Days 3-5)

### Rule 2.1: Implement Real Detection Tuning
**Requirement**: Enhance PySceneDetect with adaptive params for better scene variety.

**Implementation Steps**: 
- Add duration-based min_scene_len in _detect_scenes_real.
- Use GPT for initial descriptions if Memories.ai placeholder called.

**Code Example** (utils.py):
```python
def _detect_scenes_real(path):
    # Adaptive min len
    video_info = get_video_info(path)
    fps = video_info['fps']
    min_len = max(30, int(video_info['duration'] / 50))  # Adaptive
    detector = ContentDetector(threshold=config.SCENE_DETECTION_THRESHOLD, min_scene_len=min_len * fps)
    # ... detect and score
```

**Testing**: 
- Assert more scenes for longer videos; descriptions from GPT non-empty.
- Integration: Full workflow with real clip.

**Mitigation**: 
- Cap max scenes to avoid overload; fallback mocks.

### Rule 2.2: Refine Prompts and Add Effects
**Requirement**: Implement basic effects with MoviePy.

**Implementation Steps**: 
- Add fade/speed to _apply_effects; call in ClipChooser post-extraction.

**Code Example** (workers.py):
```python
from moviepy.video.fx.all import fadein, speedx

def _apply_effects(self, clip_path, params):
    clip = VideoFileClip(clip_path)
    if 'fade' in params:
        clip = clip.fx(fadein, 2)
    if 'speed' in params:
        clip = clip.fx(speedx, params['speed'])
    clip.write_videofile(clip_path)
```

**Testing**: 
- Assert clip duration unchanged post-fade; speed 1.5 halves duration.
- Prompt test: "add fade, speed:1.5" applies both.

**Mitigation**: 
- Skip effects if params invalid; preserve original clip.

---

## Phase 3: Implementation - Optimization & Integration (Days 6-7)

### Rule 3.1: Auto-Chunk in Motion Scoring
**Requirement**: Automatically chunk long segments for motion analysis.

**Implementation Steps**: 
- Integrate chunk_video in calculate_motion_score.
- Use FFmpeg for chunk extraction if enabled.

**Code Example** (utils.py):
```python
def chunk_video(video_path, chunk_dur=config.VIDEO_CHUNK_SIZE):
    # Use FFmpeg for faster chunking
    if config.ENABLE_FFMPEG:
        # subprocess cmd for chunks
        ...
    # MoviePy fallback
    ...
```

**Testing**: 
- Assert chunk scores average correctly; time savings >30% with FFmpeg.
- Load test: 1hr video without errors.

**Mitigation**: 
- Mock chunks if real fails; cap max chunks.

### Rule 3.2: Integrate into Workflow
**Requirement**: Update coordinator to use new features; validate in assembly.

**Implementation Steps**: 
- Pass prompts to ClipChooser; add effects in assembly if prompted.

**Testing**: 
- End-to-end: Real video with "focus:action, add fade" yields optimized clips.
- No failures; coverage >95%.

**Mitigation**: 
- Log and skip advanced features if issues.

---

## Phase 4: Expansion - Tests, Docs, and Memories.ai Placeholder (Days 8-10)

### Rule 4.1: Update and Expand Tests
**Requirement**: Rewrite legacy tests; add Memories.ai sim.

**Implementation Steps**: 
- Update test_ultimate_coverage.py for current lines.
- Add e2e tests with Memories.ai mocks (e.g., return GPT scenes).

**Testing**: 
- All tests pass; new Memories.ai fallback tests 100%.

**Mitigation**: 
- CI enforcement for coverage.

### Rule 4.2: Enhance Documentation
**Requirement**: Add detailed guides and Memories.ai section.

**Implementation Steps**: 
- Expand README with "Prompt Guide" examples.
- Add "Future Integrations" for Memories.ai (placeholder: "Swap call_model to API when available").

**Testing**: 
- Doc validation (links work, examples run).

**Mitigation**: 
- Version docs for changes.

### Rule 4.3: Memories.ai Placeholder Activation
**Requirement**: Keep placeholder but use GPT for now; prep for switch.

**Implementation Steps**: 
- In detect_scenes_memories_ai, call GPT for scene descriptions until API ready.

**Code Example** (utils.py):
```python
def detect_scenes_memories_ai(video_path):
    if memories_available:  # Future
        # Real API call to Memories.ai
        # This will be implemented once API access is available
        api_response = memories_api_client.analyze_video(video_path)
        return parse_memories_response(api_response)
    else:
        # Use GPT as temporary placeholder
        prompt = f"Describe scenes in video file. Return JSON with scenes array containing start, end, description, mood for each scene."
        response = call_model(prompt, "gpt-4")
        try:
            scenes = json.loads(response).get("scenes", [])
            # Add motion scores using our existing calculation
            for scene in scenes:
                scene["motion_score"] = calculate_motion_score(video_path, scene.get("start", 0), scene.get("end", 30))
            return scenes
        except:
            logger.warning("GPT placeholder failed, falling back to mock scenes")
            return _generate_mock_scenes(video_path)
```

**Testing**: 
- Assert GPT fallback works; prep real API mock tests.
- Test seamless switching between placeholder and real API.

**Mitigation**: 
- Config toggle; log "Using GPT placeholder for Memories.ai".
- Fallback to mock scenes if GPT fails.

### Rule 4.4: Memories.ai Integration Preparation
**Requirement**: Prepare system architecture for Memories.ai Large Visual Memory Model integration.

**Implementation Steps**:
- Add Memories.ai API client wrapper class
- Implement response parsing for Memories.ai format
- Add configuration flags for Memories.ai features
- Create authentication handling for API keys

**Code Example** (utils.py):
```python
class MemoriesAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.memories.ai/v1"
        
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze video using Memories.ai Large Visual Memory Model
        Features: Scene detection, object recognition, visual memory queries
        """
        if not memories_available:
            raise MemoriesAINotAvailableError("Memories.ai API not available")
            
        # Future implementation will call actual API
        # For now, return structured placeholder
        return {
            "scenes": [],
            "visual_memory": {},
            "detected_objects": [],
            "narrative_structure": {}
        }
        
    def search_visual_memory(self, query: str, video_path: str) -> List[Dict]:
        """Search video content using natural language queries"""
        # Implementation placeholder for visual memory search
        pass
        
    def detect_characters(self, video_path: str) -> List[Dict]:
        """Detect and track characters throughout video"""
        # Implementation placeholder for character detection
        pass
```

**Testing**:
- Mock Memories.ai API responses for testing
- Verify graceful degradation when API unavailable
- Test configuration switching between modes

**Mitigation**:
- Comprehensive fallback to existing detection methods
- Clear logging of which detection method is active

---

## Phase 5: Advanced Features and Production Readiness (Days 11-12)

### Rule 5.1: Enhanced Video Intelligence
**Requirement**: Leverage Memories.ai capabilities for superior video understanding.

**Implementation Steps**:
- Implement character tracking across scenes
- Add visual memory search for content queries
- Enhance scene classification with visual context

**Code Example** (workers.py):
```python
class EnhancedIngestionWorker:
    def __init__(self):
        self.memories_client = MemoriesAIClient(config.MEMORIES_AI_KEY) if config.ENABLE_MEMORIES_AI else None
        
    def run(self, video_path: str) -> Dict[str, Any]:
        if self.memories_client:
            # Use Memories.ai for advanced analysis
            analysis = self.memories_client.analyze_video(video_path)
            scenes = analysis["scenes"]
            characters = self.memories_client.detect_characters(video_path)
            
            # Enhance scenes with visual memory insights
            for scene in scenes:
                scene["characters"] = self._get_scene_characters(scene, characters)
                scene["visual_elements"] = analysis["detected_objects"]
                
        else:
            # Fallback to existing detection
            scenes = detect_scenes(video_path)
            
        return {"scenes": scenes, "analysis_method": "memories_ai" if self.memories_client else "traditional"}
```

### Rule 5.2: Production Configuration
**Requirement**: Production-ready configuration and monitoring.

**Implementation Steps**:
- Add production config validation
- Implement health checks for all components
- Add performance monitoring and metrics

**Testing**:
- Load testing with various video sizes
- Monitor resource usage and API quotas
- Validate production deployment

**Mitigation**:
- Automatic fallback chains for all components
- Circuit breaker patterns for external APIs
- Comprehensive error reporting

This plan fully addresses the suggestions over 12 days, with Memories.ai as a seamless future upgrade that enhances the existing system without breaking current functionality.
