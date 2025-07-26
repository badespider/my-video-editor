# Rule Development Plan for the Multi-Agent Video Editing System

To build the multi-agent system for video editing and generation (inspired by Memories.ai's workflow: Story Analysis → Choosing Clips → Narration → BGM → Generating), we'll follow a structured rule-based development plan. This plan emphasizes modularity, testability, flexibility for model switching (e.g., to Grok-4 only), and gradual iteration to address raw footage understanding. It's divided into phases with numbered rules, implementation steps, testing requirements, and mitigations. The plan uses Python with GAME SDK, starting with mocks and expanding to real tools (e.g., MoviePy for clips, PySceneDetect for detection).

## Phase 1: Setup and Configuration (Days 1-2)

**Rule 1.1: Config-Driven Design:** All settings (models, APIs, limits) must be in config.py for easy changes without code edits.
- **Implementation Steps:** Create config.py with MODEL = "grok-4", API_KEYS, VIDEO_MAX_DURATION = 600s, USE_REAL_DETECTION = False (mock initially).
- **Testing:** Assert config loads correctly in unittests.
- **Mitigation:** Default to mocks if config values missing.

**Rule 1.2: Project Structure:** Use folders: workers/ for agents, utils/ for helpers, tests/ for unittests, backend/ for API.
- **Implementation Steps:** Initialize Git repo; add .gitignore for temp files (e.g., clips.mp4).
- **Testing:** No code yet; verify structure with script.
- **Mitigation:** Use REPL for initial tests; commit after phase.

## Phase 2: Build Core Utilities (Days 3-5)

**Rule 2.1: Model Router:** Implement call_model(prompt) in utils.py to support switching (e.g., Grok-4, OpenAI, mocks).
- **Implementation Steps:** Add API calls with backups; mock responses for no-API mode.
- **Code Example:**
```python
def call_model(prompt, model=config.MODEL):
    if model == "grok-4":
        # Real API call
        return "Grok response"
    return "Mock response"  # Fallback
```
- **Testing:** Unittests for each model; assert no errors on switch.
- **Mitigation:** Fallback to mock if API fails.

**Rule 2.2: Video Helpers:** Add functions for detect_scenes, extract_clip, assemble_clips in utils.py, mocking for REPL.
- **Implementation Steps:** Use PySceneDetect for real detection; mock random scenes for full coverage.
- **Code Example:**
```python
def detect_scenes(video_path):
    if config.USE_REAL_DETECTION:
        # PySceneDetect code
        return [{"start": 0, "end": 60}]
    # Mock
    return [{"start": 0, "end": 60}]
```
- **Testing:** Assert scenes cover >80% duration.
- **Mitigation:** Uniform division fallback.

## Phase 3: Develop Workers (Days 6-9)

**Rule 3.1: Worker Modularity:** Each worker (Ingestion, Analyzer, etc.) must be a class with run method; share state via dict.
- **Implementation Steps:** Update Ingestion to call detect_scenes; ClipChooser to select/extract diverse clips.
- **Code Example (workers.py):**
```python
class IngestionWorker:
    def run(self, video_path):
        scenes = utils.detect_scenes(video_path)
        return {"scenes": scenes}
```
- **Testing:** Individual unittests; assert full video coverage.
- **Mitigation:** Score-based selection to avoid early bias.

**Rule 3.2: Clip Diversity:** Select clips from high-score scenes across thirds; ensure ≥80% coverage.
- **Implementation Steps:** Add _select_diverse_scenes in ClipChooser.
- **Code Example:**
```python
def _select_diverse_scenes(self, scenes, duration):
    # Sort and select per third
    return scenes  # Placeholder
```
- **Testing:** Assert clips from start/middle/end.
- **Mitigation:** Add low-score scenes if coverage low.

**Rule 3.3: Assembly Rules:** Concatenate clips with narration/BGM; validate full duration.
- **Implementation Steps:** Update AssemblyWorker to use assemble_clips.
- **Testing:** End-to-end with mock video.
- **Mitigation:** Log if assembly fails.

## Phase 4: Integration and API (Days 10-12)

**Rule 4.1: Coordinator Rules:** VideoAgent chains workers; validate coverage in run_with_video.
- **Implementation Steps:** Add checks in _verify_final_plan.
- **Code Example (coordinator.py):**
```python
def run_with_video(self, video_path):
    ingestion = IngestionWorker().run(video_path)
    # Chain to others
    return result
```
- **Testing:** Integration tests for full workflow.
- **Mitigation:** Retry if coverage <80%.

**Rule 4.2: Backend Endpoints:** Use FastAPI for /generate (POST video_path or script).
- **Implementation Steps:** Add in api.py; call VideoAgent.
- **Testing:** Test endpoints with curl.
- **Mitigation:** Rate limit API.

## Phase 5: Cleanup and Expansion (Days 13-14)

**Rule 5.1: Mock Cleanup:** Run cleanup_mocks() post-run to delete temp clips/files.
- **Implementation Steps:** Add in main.py.
- **Code Example:**
```python
def cleanup_mocks():
    for file in os.listdir("temp"):
        os.remove(file)
```
- **Testing:** Assert no mocks left after run.
- **Mitigation:** Only in dev mode.

**Rule 5.2: Model Switch Testing:** Test with Grok-4; update config.
- **Implementation Steps:** Run workflow with MODEL = "grok-4".
- **Testing:** Assert same outputs format.
- **Mitigation:** Backup model if switch fails.

## Overall Rules

**Testing Rule:** 100% pass before task switch; use unittests/integration.
**Mitigation Rule:** Mocks for dev; real in prod via config.
**Expansion Rule:** After MVP, add Memories.ai when available by updating MODEL to "memories-ai" and API calls.
