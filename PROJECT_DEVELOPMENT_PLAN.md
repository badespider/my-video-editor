# Project Development Plan

## Phase 1: Planning and Setup (Days 1-2)

### Rule 1.1: Define Backend Architecture

- **Requirement**: Backend must handle sessions (video state, edit history) via WebSocket, with REST fallback for uploads.

- **Implementation Steps**:
  - Setup FastAPI with `/ws/edit` for chat, `/upload/video` for files.
  - Add session store (e.g., in-memory dict for MVP; Redis for prod).

- **Code Example (backend/api.py - Extend existing)**:
  
  ```python
  from fastapi import WebSocket, UploadFile
  sessions = {}  # {session_id: {"video_path": str, "edits": list, "preview_path": str}}

  @app.websocket("/ws/edit/{session_id}")
  async def websocket_endpoint(websocket: WebSocket, session_id: str):
      await websocket.accept()
      if session_id not in sessions:
          sessions[session_id] = {"video_path": None, "edits": [], "preview_path": None}
      while True:
          data = await websocket.receive_text()
          # Parse and apply edit...
          await websocket.send_text("Edit applied. Preview updated.")

  @app.post("/upload/video")
  async def upload_video(file: UploadFile):
      session_id = str(uuid.uuid4())
      path = f"temp/{file.filename}"
      with open(path, "wb") as f:
          f.write(await file.read())
      sessions[session_id] = {"video_path": path, "edits": [], "preview_path": path}
      return {"session_id": session_id}
  ```

- **Testing**:
  - Unittest WebSocket connect/disconnect; assert session created on upload.
  - Metric: <1s latency for chat responses.

- **Mitigation**:
  - Session timeout (30min); log invalid sessions.

### Rule 1.2: Memories.ai Placeholder Prep

- **Requirement**: Reserve hooks for Memories.ai in analysis, using GPT for now.

- **Implementation Steps**:
  - Add call_memories_placeholder in utils.py (GPT proxy).

- **Code Example (utils.py)**:

  ```python
  def call_memories_placeholder(video_path, query):
      if config.ENABLE_MEMORIES_AI:
          # Future real API
          pass
      else:
          prompt = f"Analyze video {video_path} for {query} using GPT simulation."
          return call_model(prompt, "gpt-4")
  ```

- **Testing**:
  - Assert GPT fallback works; placeholder returns mock analysis.
  - Unittest toggle.

- **Mitigation**:
  - Always fallback to GPT; log "Memories.ai simulation mode".

### Rule 1.3: Config & Security Setup

- **Requirement**: Secure uploads/chats; add edit limits.

- **Implementation Steps**:
  - Config: MAX_EDITS=20, SESSION_TIMEOUT=1800.

- **Testing**:
  - Assert file size < MAX_VIDEO_SIZE; rate-limit chats.

- **Mitigation**:
  - Validate uploads (MP4 only); sanitize inputs.

## Phase 2: Chat & Command Parsing (Days 3-5)

### Rule 2.1: Natural Language Command Parsing

- **Requirement**: Parse chats to edit ops (e.g., "trim 10s" → {"type": "trim", "start": 10}).

- **Implementation Steps**:
  - Use call_model to parse; validate ops.

- **Code Example (coordinator.py - Extend VideoAgent)**:

  ```python
  def parse_command(self, message: str) -> dict:
      prompt = f"Parse video edit command: {message}. Return JSON: {{type: str, params: dict}}."
      response = call_model(prompt, "gpt-4")
      return json.loads(response)
  ```

- **Testing**:
  - Assert "trim intro 20s" → {"type": "trim", "params": {"start": 20}}.
  - 100% accuracy in 15 test messages.

- **Mitigation**:
  - Rule-based fallback for common ops; ask clarification if invalid.

### Rule 2.2: Apply Iterative Edits

- **Requirement**: Cumulative edits on video state; generate preview MP4.

- **Implementation Steps**:
  - In WS handler, parse → apply (e.g., trim via MoviePy) → update preview.

- **Code Example (api.py - WS Handler Update)**:

  ```python
  async def websocket_endpoint(websocket: WebSocket, session_id: str):
      # ...
      data = await websocket.receive_text()
      command = agent.parse_command(data)
      if command['type'] == 'trim':
          params = command['params']
          new_path = trim_video(sessions[session_id]['preview_path'], params['start'], params['end'])
          sessions[session_id]['preview_path'] = new_path
          sessions[session_id]['edits'].append(command)
      await websocket.send_json({"preview_url": f"/preview/{session_id}"})
  ```

- **Testing**:
  - Chain edits: Trim then overlay; assert preview updates.
  - Metric: Preview gen <5s for 1min video.

- **Mitigation**:
  - Undo via pop edits; limit history to 10.

## Phase 3: Preview & Finalization (Days 6-7)

### Rule 3.1: Real-Time Preview Generation

- **Requirement**: Serve temp previews via /preview/{id}.

- **Implementation Steps**:
  - Add FastAPI endpoint for streaming MP4.

- **Code Example (api.py)**:

  ```python
  @app.get("/preview/{session_id}")
  def get_preview(session_id: str):
      path = sessions.get(session_id, {}).get('preview_path')
      if path:
          return FileResponse(path, media_type="video/mp4")
      raise HTTPException(404)
  ```

- **Testing**:
  - Assert 200 OK for valid; 404 for missing.
  - Integration: Chat → Edit → Preview URL works.

- **Mitigation**:
  - Cache previews; delete on session end.

### Rule 3.2: Finalization & Export

- **Requirement**: On "done", compile final MP4 from state.

- **Implementation Steps**:
  - Apply all edits in batch; use assemble_clips.

- **Code Example (coordinator.py)**:

  ```python
  def finalize_video(self, session_id: str) -> str:
      state = sessions[session_id]
      final_path = "final_" + str(uuid.uuid4()) + ".mp4"
      clip = VideoFileClip(state['video_path'])
      for edit in state['edits']:
          # Apply each...
      clip.write_videofile(final_path)
      return final_path
  ```

- **Testing**:
  - Assert final MP4 has all edits; duration matches.
  - End-to-end chat session to export.

- **Mitigation**:
  - If compile fails, return latest preview.

## Phase 4: Integration & AI Suggestions (Days 8-9)

### Rule 4.1: Proactive AI Suggestions

- **Requirement**: Agent analyzes video/edits and suggests (e.g., "Add fade?").

- **Implementation Steps**:
  - After each edit, call GPT for suggestions based on state.

- **Code Example (WS Handler)**:

  ```python
  # After edit
  suggestion = call_model(f"Suggest improvements for video with edits: {state['edits']}", "gpt-4")
  await websocket.send_text(f"Suggestion: {suggestion}")
  ```

- **Testing**:
  - Assert relevant suggestions (e.g., dark video → "enhance brightness").
  - Mock GPT for consistency.

- **Mitigation**:
  - Optional (config ENABLE_SUGGESTIONS=True); limit to 3/turn.

### Rule 4.2: Memories.ai Placeholder

- **Requirement**: Use GPT for analysis now; prep switch.

- **Implementation Steps**:
  - In analysis, call placeholder (GPT prompt: "Analyze scene for objects").

- **Testing**:
  - Assert placeholder enhances descriptions (e.g., add "objects: car, person").

- **Mitigation**:
  - Toggle; fallback to basic analysis.

## Phase 5: Testing & Deployment Prep (Days 10-12)

### Rule 5.1: Comprehensive Testing

- **Requirement**: Cover chat flows, errors, and performance.

- **Implementation Steps**:
  - Add WS tests (e.g., websocket-client); stress with 20 edits.

- **Testing**:
  - E2e: Upload → Chat edits → Finalize (assert MP4 valid).
  - Coverage >95%; latency <5s.

- **Mitigation**:
  - Log all sessions for debugging.

### Rule 5.2: Docs & Deployment

- **Requirement**: Update README with backend setup; add Docker.

- **Implementation Steps**:
  - Dockerfile for FastAPI; guide for running WS.

- **Testing**:
  - Deploy local; assert WS connects.

- **Mitigation**:
  - Env vars for secrets.

This plan builds a robust backend MVP.

