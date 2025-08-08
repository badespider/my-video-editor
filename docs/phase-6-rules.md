# Rule Development Plan: Phase 6 - AI Backend Integration, Testing, and Multi-User Authentication

## Purpose
This rule plan outlines the next phase of development for the AI Video Editing System, focusing on replacing AI placeholders with real backend integrations (e.g., Memories.ai API), conducting thorough testing with sample videos (vlogs and movies), and enhancing session management with user authentication to support multi-user scenarios. This builds on previous phases (e.g., Phase 5: Testing & Deployment) and addresses scalability, reliability, and security needs.

The plan introduces **Rule 6.1: AI Integration and Testing** and **Rule 6.2: Multi-User Authentication**, ensuring structured, iterative implementation while maintaining backward compatibility and high test coverage.

## Core Principles
- **Modularity**: Keep integrations swappable (e.g., via config.py) to allow for alternative AI providers.
- **Security First**: Authentication must prevent session hijacking and ensure data isolation.
- **Test-Driven**: All changes require 90%+ coverage, with E2E tests for real-world scenarios.
- **Backward Compatibility**: Placeholders remain as fallbacks during transition.
- **Performance**: Integrations should not exceed 10s latency for API calls; add timeouts and retries.

## Rule 6.1: AI Backend Integration and Testing
### Objective
Replace placeholders (e.g., call_memories_placeholder in utils/utils.py) with actual Memories.ai API calls for video analysis, suggestions, and optimizations. Test rigorously using sample vlogs/movies to validate editing for diverse content types.

### Guidelines
- Use environment variables (e.g., MEMORIES_AI_KEY in .env) for API credentials.
- Handle API errors gracefully: Fallback to placeholders on failure, log via logging.getLogger.
- Rate limiting: Implement client-side throttling (e.g., 5 calls/min) to avoid API abuse.
- Data Privacy: Anonymize video metadata before sending to API; comply with GDPR-like standards (reference SECURITY_GUIDE.md).
- Testing Scope: Cover 80% happy paths (successful edits) and 20% edge cases (e.g., long videos, poor quality).

### Implementation Steps
1. **API Integration**:
   - Update config.py: Add MEMORIES_AI_BASE_URL = "https://api.memories.ai/v1" and related configs.
   - Modify utils/utils.py:
     - Replace call_memories_placeholder with async def call_memories_api(endpoint: str, payload: dict):
       - Use aiohttp for async requests: session.post(url, json=payload, headers={"Authorization": f"Bearer {config.MEMORIES_AI_KEY}"}).
       - Endpoints: /analyze for analysis, /suggest-edits for suggestions, /optimize for recommendations.
     - Add payload formatting: e.g., for video analysis, upload video snippets (limit to 30s previews) or send metadata.
   - Update backend/workflow_orchestrator.py and api.py handlers (e.g., _get_video_analysis) to call the new function.

2. **Fallback Mechanism**:
   - In call_memories_api, wrap in try-except: On HTTPError or timeout, log and call original placeholder.
   - Config flag: USE_REAL_AI = True (default False during dev).

3. **Sample Data Preparation**:
   - Use anime_script.txt and video_plan.json as bases.
   - Add test assets: Create /samples/ dir with vlog.mp4 (short travel vlog) and movie_clip.mp4 (action scene excerpt).
   - Generate test plans: e.g., For vlog: "Condense to 5min highlights"; For movie: "Extract dramatic scenes".

4. **Integration Points**:
   - In coordinator.py (VideoAgent): Use API for parse_command if natural language involves analysis.
   - In workers/workers.py: Parallelize API calls for multi-clip processing.

### Testing Plan
- **Unit Tests**: Add to tests/test_utils.py: Mock API responses (using responses lib) for call_memories_api.
- **Integration Tests**: In tests/test_backend_integration.py: Upload sample vlog, trigger /analyze, assert results match expected (e.g., scenes detected).
- **E2E Tests**: Update .github/workflows/video-tests.yml: Run with real API (use test key), compare outputs against baselines (e.g., anime_video_analysis.json).
- **Edge Cases**: Test with invalid API key (fallback triggers), network failure, oversized videos (chunking logic).
- **Metrics**: Aim for <5s avg response time; track in docs/test_coverage_progress.md.
- **Sample Runs**: Use main.py or create_video.py with samples; output to phase6_test_report.json.

## Rule 6.2: Multi-User Authentication with JWT
### Objective
Enhance session_manager.py to support user-based sessions, preventing cross-user access and enabling multi-user deployments.

### Guidelines
- Use JWT for stateless auth: No server-side token storage.
- Token Expiration: 1h for sessions, refresh via /auth/refresh.
- Role-Based: Basic roles (user, admin); Users own their sessions.
- Security: Validate tokens on all endpoints/WS; Use HS256 algorithm.
- Audit: Log auth events; Integrate with existing WS_TOKEN_VALIDATION.

### Implementation Steps
1. **Dependencies**:
   - Add to requirements.txt: PyJWT==2.8.0, cryptography==42.0.5.

2. **Auth Endpoints in backend/api.py**:
   - POST /auth/login: Accept username/password, return JWT if valid (mock users in config.py for dev).
   - POST /auth/refresh: Validate refresh token, issue new access token.
   - Use fastapi.security.HTTPBearer for protected routes.

3. **Session Enhancements in session_manager.py**:
   - Add user_id: str to SessionData.
   - create_session: Require user_id from decoded JWT.
   - get_session: Validate session.user_id matches request user's ID.
   - JWT Utils: def generate_jwt(user_id: str) -> str: Use jwt.encode with secret from config.JWT_SECRET.
   - Middleware: In api.py, add Depends(oauth2_scheme) to endpoints; Decode and attach user_id to request.state.

4. **WebSocket Auth**:
   - In ws/{session_id}: Require ?token= query param; Validate JWT before registering.
   - Update _handle_* functions: Check request.state.user_id owns session.

5. **Migration**:
   - For existing sessions: Assign to a default 'guest' user_id during upgrade.

### Testing Plan
- **Unit Tests**: tests/test_session_manager.py: Mock JWT encode/decode; Test invalid/expired tokens raise 401.
- **Integration Tests**: tests/test_api.py: Login -> Create session -> Edit (with token) -> Attempt cross-user access (fails).
- **Security Tests**: Fuzz tokens; Test brute-force resistance (add rate limiting via fastapi-limiter).
- **Multi-User Simulation**: In tests/test_e2e_workflow_api.py: Spawn multiple users, ensure session isolation.
- **Coverage**: Update pytest.ini; Run with --cov; Document in docs/test_completion_summary.md.

## Timeline and Milestones
- Week 1: AI Integration (Rule 6.1 steps 1-2) + Basic Tests.
- Week 2: Sample Testing (Rule 6.1 steps 3-4) + Full Coverage.
- Week 3: Auth Implementation (Rule 6.2 steps 1-5) + Security Audit.
- Week 4: E2E Multi-User Tests + Deployment Guide Update.
- Completion: Update PHASE6_COMPLETION.md; Merge to main after 100% test pass.

## Risks and Mitigations
- API Downtime: Use mocks in tests; Fallbacks in prod.
- Auth Bugs: Start with dev-only; Use OWASP guidelines.
- Performance: Profile API calls; Optimize with caching (Redis).

This plan ensures a smooth transition to production-ready features. If needed, reference existing docs like IMPLEMENTATION_SUMMARY.md for patterns.

