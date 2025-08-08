import asyncio
import json
import os
import time
import types
import pytest
from unittest.mock import patch

# We will test the high-level behavior of call_memories_api:
# - Falls back to placeholder when USE_REAL_AI is False or missing key
# - Attempts aiohttp POST when enabled (we'll mock aiohttp)
# - On error, falls back to placeholder

@pytest.mark.asyncio
async def test_call_memories_api_fallback_when_disabled(monkeypatch):
    from utils import utils as U

    # Ensure fallback path
    # Ensure fallback path by patching global config module
    import config as _cfg
    monkeypatch.setattr(_cfg, "USE_REAL_AI", False, raising=False)
    monkeypatch.setattr(_cfg, "MEMORIES_AI_KEY", "", raising=False)

    # Spy on placeholder
    calls = {"count": 0}
    def placeholder(video_path_or_payload, detailed=True):
        calls["count"] += 1
        return {"placeholder": True}
    monkeypatch.setattr(U, "call_memories_placeholder", placeholder, raising=True)

    result = await U.call_memories_api("analyze", {"video_path": "x.mp4", "detailed": True})
    assert result == {"placeholder": True}
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_call_memories_api_success(monkeypatch):
    from utils import utils as U

    # Configure to enable real path
    import config as _cfg
    monkeypatch.setattr(_cfg, "USE_REAL_AI", True, raising=False)
    monkeypatch.setattr(_cfg, "MEMORIES_AI_KEY", "test", raising=False)
    monkeypatch.setattr(_cfg, "MEMORIES_AI_BASE_URL", "https://example.test/v1", raising=False)
    monkeypatch.setattr(_cfg, "API_TIMEOUT", 5, raising=False)

    # Mock aiohttp session/post
    class MockResp:
        def __init__(self, status=200, payload=None):
            self.status = status
            self._payload = payload or {"ok": True}
        async def json(self):
            return self._payload
        async def text(self):
            return json.dumps(self._payload)
    class MockSession:
        def __init__(self, *a, **kw):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        def post(self, url, json=None, headers=None):
            class Ctx:
                async def __aenter__(self_inner):
                    return MockResp(200, {"ok": True, "url": url, "json": json})
                async def __aexit__(self_inner, exc_type, exc, tb):
                    return False
            return Ctx()
    class MockTimeout:
        def __init__(self, total=None):
            self.total = total

    # Inject mock aiohttp module into sys.modules so import inside function picks it up
    import types as _types
    import sys as _sys
    mock_aiohttp = _types.SimpleNamespace(ClientSession=MockSession, ClientTimeout=MockTimeout)
    monkeypatch.setitem(_sys.modules, 'aiohttp', mock_aiohttp)

    out = await U.call_memories_api("analyze", {"video_path": "x.mp4", "detailed": True})
    assert out["ok"] is True
    assert "url" in out and out["url"].endswith("/analyze")


@pytest.mark.asyncio
async def test_call_memories_api_http_error_falls_back(monkeypatch):
    from utils import utils as U

    import config as _cfg
    monkeypatch.setattr(_cfg, "USE_REAL_AI", True, raising=False)
    monkeypatch.setattr(_cfg, "MEMORIES_AI_KEY", "test", raising=False)
    monkeypatch.setattr(_cfg, "MEMORIES_AI_BASE_URL", "https://example.test/v1", raising=False)
    monkeypatch.setattr(_cfg, "API_TIMEOUT", 5, raising=False)

    # Mock aiohttp to return error
    class MockResp:
        def __init__(self, status=500):
            self.status = status
        async def json(self):
            return {"ok": False}
        async def text(self):
            return "server error"
    class MockSession:
        def __init__(self, *a, **kw):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        def post(self, url, json=None, headers=None):
            class Ctx:
                async def __aenter__(self_inner):
                    return MockResp(500)
                async def __aexit__(self_inner, exc_type, exc, tb):
                    return False
            return Ctx()
    class MockTimeout:
        def __init__(self, total=None):
            self.total = total

    # Inject mock aiohttp module into sys.modules so import inside function picks it up
    import types as _types
    import sys as _sys
    mock_aiohttp = _types.SimpleNamespace(ClientSession=MockSession, ClientTimeout=MockTimeout)
    monkeypatch.setitem(_sys.modules, 'aiohttp', mock_aiohttp)

    # Placeholder spy
    calls = {"count": 0}
    def placeholder(video_path_or_payload, detailed=True):
        calls["count"] += 1
        return {"placeholder": True}
    monkeypatch.setattr(U, "call_memories_placeholder", placeholder, raising=True)

    out = await U.call_memories_api("analyze", {"video_path": "x.mp4", "detailed": True})
    assert out == {"placeholder": True}
    assert calls["count"] == 1

