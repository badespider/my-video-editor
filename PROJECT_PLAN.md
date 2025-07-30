# Phase 1: Planning and Setup (Days 1-2)

## Rule 1.1: Fix Dependency Failures in Tests/CI

**Requirement:** Ensure all tests pass without MoviePy/FFmpeg by expanding mocks; matrix CI for dep-free runs.

### Implementation Steps:

- Update mocks/video_shims.py to cover more ops (e.g., trim returns mock path).
- In ci.yml/video-tests.yml, add dep installs only for full-env; mock all in dep-free.

**Code Example (mocks/video_shims.py - Expand):**

```python
def mock_trim_video(input_path, start, end, output_path):
    # Mock trim: Create placeholder
    with open(output_path, 'w') as f:
        f.write(f"Mock trimmed from {start} to {end}")
    return output_path
```

### Testing:

- Assert all tests pass in mock mode (100% in reports); CI green on push.
- Unittest mocks (e.g., mock_trim creates file).

### Mitigation:

- Env var MOCK_FFMPEG=1 forces mocks; log "Mock mode enabled".

## Rule 1.2: Enhance Memories.ai Placeholder

**Requirement:** Make placeholder more active with GPT prompts for real sim; add key validation.

### Implementation Steps:

- Update call_memories_placeholder to use detailed GPT prompts (e.g., "Simulate Memories.ai: Detect objects/moods").
- Add config check in /analyze (raise if no key but enabled).

**Code Example (utils.py - Update Placeholder):**

```python
def call_memories_placeholder(video_path, query):
    if config.MEMORIES_API_KEY and config.ENABLE_MEMORIES_AI:
        # Future real
        pass
    prompt = f"Simulate Memories.ai analysis for {video_path}: {query}. Return detailed JSON."
    return json.loads(call_model(prompt, "gpt-4"))
```

### Testing:

- Assert sim returns structured data (e.g., "objects: car"); key validation raises 400 in endpoint.
- Integration: /analyze uses sim if no key.

### Mitigation:

- Always fallback to GPT; log "Placeholder active—no API key".

## Rule 1.3: Address Edit/Preview Limitations Prep

**Requirement:** Add range checks to edits; enable streaming for large previews.

### Implementation Steps:

- Update _apply_trim_command to validate (end > start); add Range headers in /preview.

**Code Example (api.py - Preview Update):**

```python
from fastapi.responses import StreamingResponse

@app.get("/preview/{session_id}")
def get_preview(session_id: str, range: str = Header(None)):
    path = sessions[session_id]['preview_path']
    if range:
        # Parse Range: bytes=start-end
        start, end = map(int, range.replace("bytes=", "").split("-"))
        return StreamingResponse(open(path, 'rb'), media_type="video/mp4", headers={"Content-Range": f"bytes {start}-{end}/*"})
    return FileResponse(path)
```

### Testing:

- Assert invalid trim raises ValueError; streaming returns partial bytes.
- E2e: Trim with invalid → error response.

### Mitigation:

- Default full file if no Range; limit preview size.

## Rule 1.4: Scalability Edges Setup

**Requirement:** Switch to Redis for sessions; add auth to WS.

### Implementation Steps:

- Install redis-py; update sessions to Redis client.
- Add token param to WS (validate in connect).

**Code Example (api.py - Redis/WS Update):**

```python
import redis
r = redis.Redis(host='localhost', port=6379)

@app.websocket("/ws/edit/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, token: str = Query()):
    if token != "valid_token":  # Future JWT
        await websocket.close(code=1008)
        return
    # Use r.get/set for sessions
```

### Testing:

- Assert Redis stores sessions; invalid token closes WS.

### Mitigation:

- Fallback to in-memory if no Redis; rate-limit WS connects.

## Rule 1.5: Testing Gaps Preparation

**Requirement:** Plan WS e2e and un-skip tests.

### Implementation Steps:

- List gaps; draft WS tests in test_phase3_api.py.

### Testing:

- Baseline coverage.

### Mitigation:

- Incremental additions.

# Phase 2: Implementation - Dep Fixes 6 Memories.ai (Days 3-5)

## Rule 2.1: Resolve Dep Failures

**Requirement:** Expand mocks to cover all MoviePy/FFmpeg paths.

### Implementation Steps:

- Add mocks for finalize/trim in video_shims.py; use in conftest.py fixtures.

**Code Example (mocks/video_shims.py):**

```python
def mock_generate_thumbnail(...):
    with open(output_path, 'w') as f:
        f.write("Mock thumbnail")
    return output_path
```

### Testing:

- Assert full-env CI green; mock mode 100%.

### Mitigation:

- Conditional imports; log dep status.

## Rule 2.2: Activate Memories.ai Sim Enhancements

**Requirement:** Use detailed GPT prompts for better sim.

### Implementation Steps:

- Enhance prompts in placeholder; test in /analyze.

**Code Example (utils.py):**

```python
prompt = f"Act as Memories.ai: For {video_path}, detect {query} like objects, moods, actions. JSON format."
```

### Testing:

- Assert returns "objects: car, mood: intense"; compare to basic GPT.

### Mitigation:

- Cache sim results; toggle off if slow.

# Phase 3: Implementation - Edits, Previews, 6 Scalability (Days 6-7)

## Rule 3.1: Fix Edit/Preview Limitations

**Requirement:** Add checks and streaming support.

### Implementation Steps:

- Implement Range in /preview; validate in apply_command.

### Testing:

- Assert invalid end<start errors; streaming partial MP4.
- E2e: Chat trim → streamed preview.

### Mitigation:

- Fallback to full if Range invalid.

## Rule 3.2: Address Scalability Edges

**Requirement:** Integrate Redis and WS auth.

### Implementation Steps:

- Config REDIS_URL; update sessions/workers to use Redis.

### Testing:

- Assert Redis persists across restarts; invalid token 1008 close.

### Mitigation:

- In-memory fallback; limit sessions via config.

# Phase 4: Implementation - Testing Gaps (Days 8-9)

## Rule 4.1: Close Testing Gaps

**Requirement:** Un-skip tests; add WS e2e.

### Implementation Steps:

- Rename test_api.py.skip to .py; add WS tests with websocket-client.

**Code Example (test_phase3_api.py - WS Test):**

```python
import websocket

def test_websocket():
    ws = websocket.WebSocket()
    ws.connect("ws://localhost:8000/ws/edit/test_id?token=valid")
    ws.send("trim 10s")
    response = ws.recv()
    assert "applied" in response
    ws.close()
```

### Testing:

- All tests pass; new WS coverage >90%.

### Mitigation:

- Mock WS for CI.

# Phase 5: Final Review 6 Deployment Prep (Day 10)

## Rule 5.1: System-Wide Validation

**Requirement:** Run all tests; benchmark improvements.

### Implementation Steps:

- Execute pytest; log results.

### Testing:

- 100% pass; compare to previous (e.g., no dep failures).

### Mitigation:

- Fix any regressions.
