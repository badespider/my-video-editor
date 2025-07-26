# Multimodal Video Creation Plan

## Key Areas of Development

### 1. Incorporate Raw Footage Handling
- Simulate Memories.ai's indexing (mock for now)
- Plan to swap with a real API or alternatives like Google Video Intelligence later

### 2. Ensure Model Flexibility
- Use a config-driven router to switch models (e.g., Grok-4, OpenAI)

### 3. Expand to Full Workflow
- Move beyond planning to mock video output
- Prepare for real video generation

### 4. Connect to Frontend/Backend
- Use REST APIs for UI integration (e.g., on Lovable/Bolt.new)

### 5. Clean Mocks
- Automate mock data deletion post-deployment

## Updated Multi-Agent System Design with Rules

### Design Overview

**Objective:** Build a multi-agent system that processes raw footage or story scripts into a video plan and eventually a mock video file, with flexibility to switch AI models and simulate deep footage understanding.

**Framework:** GAME SDK (Python)

### Agents:
- **Coordinator (HLP):** Orchestrates tasks: Ingestion → Analysis → Clip Selection → Narration → BGM → Assembly.
- **Ingestion Worker:** Simulates indexing raw footage
- **Story Analyzer Worker:** Parses scripts or indexed data into scenes/rationale
- **Clip Chooser Worker:** Generates clip descriptions or mocks
- **Narration Generator Worker:** Creates narration scripts
- **BGM Selector Worker:** Suggests music based on mood
- **Video Assembler Worker:** Outputs JSON plan or mock video file

### Model Flexibility
- Config-driven (e.g., `MODEL = "grok-4"`)

### Frontend/Backend
- REST APIs (Flask) for UI integration

### Rules Recap (Updated with Your Feedback)

**General Design:**
- Modular
- Model-Agnostic: Use config.py for model routing
- Validate outputs
- Start simple with JSON plans, expand to mock video

**Development:**
- Python 3.12+, GAME SDK
- TDD 
- Error Handling
- Git versioning

**Workflow:**
- Sequential Ingestion → Analysis → Clips → Narration → BGM → Assembly

**Backend-Frontend Connectivity:**
- Backend: Flask/FastAPI
- Frontend: REST API calls

**Raw Footage Handling:**
- Mock indexing with plans to use real APIs

**Example Mock:**
```json
{
 "scenes": [
 {"start": "00:00:00", "end": "00:01:30", "description": "Intro at beach"},
 {"start": "00:01:30", "end": "00:03:00", "description": "Exploring market"},
 {"start": "00:03:00", "end": "00:05:00", "description": "Sunset reflection"}
 ]
}
```

Prepare for transcription or frame analysis to understand footage context.
