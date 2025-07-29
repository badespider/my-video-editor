#!/usr/bin/env python3
"""
Demo script showing how to use Phase 3 API endpoints.
Provides examples of API calls for video editing functionality.
"""

import asyncio
import requests
import json
import time
import os
from pathlib import Path

# API Base URL (adjust if running on different host/port)
API_BASE = "http://localhost:8000"

async def demo_phase3_api_usage():
    """Demonstrate Phase 3 API endpoints with example usage."""
    
    print("=== Phase 3 API Usage Demo ===")
    print(f"API Base URL: {API_BASE}")
    
    # Note: This demo shows the API calls structure
    # In a real scenario, you'd need a running FastAPI server and a real video session
    
    print("\n1. Video Upload and Session Creation")
    print("   POST /upload/video")
    print("   Example:")
    upload_example = {
        "method": "POST",
        "url": f"{API_BASE}/upload/video",
        "files": {"file": ("video.mp4", "video_binary_data", "video/mp4")},
        "expected_response": {
            "session_id": "uuid-session-id",
            "filename": "sanitized_filename.mp4"
        }
    }
    print(f"   {json.dumps(upload_example, indent=6)}")
    
    print("\n2. Real-time Editing via WebSocket")
    print("   WebSocket: /ws/edit/{session_id}")
    print("   Example commands:")
    websocket_examples = [
        "trim the video from 0:30 to 1:45",
        "remove the section from 2:00 to 2:15",
        "cut out the first 10 seconds",
    ]
    for cmd in websocket_examples:
        print(f"   → \"{cmd}\"")
    
    print("\n3. Video Trimming")
    print("   POST /trim/{session_id}")
    trim_example = {
        "method": "POST",
        "url": f"{API_BASE}/trim/session-id-here",
        "json": {
            "start_time": "00:00:30",
            "end_time": "00:01:45"
        },
        "expected_response": {
            "status": "success",
            "output_path": "trimmed_session-id_timestamp.mp4",
            "preview_url": "/preview/session-id",
            "edit_applied": {
                "type": "trim",
                "start_time": "00:00:30",
                "end_time": "00:01:45",
                "timestamp": 1700000000.0
            }
        }
    }
    print(f"   {json.dumps(trim_example, indent=6)}")
    
    print("\n4. Batch Edit Commands")
    print("   POST /apply_edits/{session_id}")
    batch_edit_example = {
        "method": "POST",
        "url": f"{API_BASE}/apply_edits/session-id-here",
        "json": {
            "edits": [
                {"cmd": "trim", "start": "00:00:10", "end": "00:01:00"},
                {"cmd": "trim", "start": "00:00:05", "end": "00:00:45"}
            ]
        },
        "expected_response": {
            "status": "success",
            "output_path": "edited_session-id_timestamp.mp4",
            "preview_url": "/preview/session-id",
            "edits_applied": 2,
            "edit_record": {
                "type": "batch_edits",
                "edits": "...",
                "timestamp": 1700000000.0
            }
        }
    }
    print(f"   {json.dumps(batch_edit_example, indent=6)}")
    
    print("\n5. Thumbnail Generation")
    print("   POST /thumbnail/{session_id}")
    thumbnail_example = {
        "method": "POST",
        "url": f"{API_BASE}/thumbnail/session-id-here",
        "json": {
            "time": "00:00:30"
        },
        "expected_response": {
            "status": "success",
            "thumbnail_path": "thumb_session-id_timestamp.jpg",
            "thumbnail_url": "/file/thumb_session-id_timestamp.jpg",
            "time": "00:00:30"
        }
    }
    print(f"   {json.dumps(thumbnail_example, indent=6)}")
    
    print("\n6. Preview Video Access")
    print("   GET /preview/{session_id}")
    print("   Returns: Video file (MP4) for real-time preview")
    print("   Content-Type: video/mp4")
    
    print("\n7. File Serving (Thumbnails, Processed Videos)")
    print("   GET /file/{filename}")
    print("   Examples:")
    file_examples = [
        f"{API_BASE}/file/thumb_session-id_timestamp.jpg",
        f"{API_BASE}/file/trimmed_session-id_timestamp.mp4",
        f"{API_BASE}/file/edited_session-id_timestamp.mp4"
    ]
    for url in file_examples:
        print(f"   → {url}")
    
    print("\n8. Video Finalization")
    print("   POST /finalize/{session_id}")
    finalize_example = {
        "method": "POST",
        "url": f"{API_BASE}/finalize/session-id-here",
        "expected_response": {
            "status": "success",
            "final_video_path": "path/to/final/video.mp4",
            "edits_applied": 3,
            "session_id": "session-id-here"
        }
    }
    print(f"   {json.dumps(finalize_example, indent=6)}")
    
    print("\n9. Session Information")
    print("   GET /session/{session_id}")
    session_info_example = {
        "method": "GET",
        "url": f"{API_BASE}/session/session-id-here",
        "expected_response": {
            "session_id": "session-id-here",
            "filename": "original_video.mp4",
            "edits_count": 3,
            "finalized": False,
            "last_activity": 1700000000.0,
            "file_size": 1024000
        }
    }
    print(f"   {json.dumps(session_info_example, indent=6)}")
    
    print("\n=== Phase 3 API Integration Examples ===")
    
    print("\n🔧 Python Client Example:")
    python_example = '''
import requests
import json

# 1. Upload video and create session
with open("video.mp4", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload/video",
        files={"file": ("video.mp4", f, "video/mp4")}
    )
    session_data = response.json()
    session_id = session_data["session_id"]

# 2. Trim the video
trim_response = requests.post(
    f"http://localhost:8000/trim/{session_id}",
    json={"start_time": "00:00:10", "end_time": "00:01:30"}
)

# 3. Generate thumbnail
thumb_response = requests.post(
    f"http://localhost:8000/thumbnail/{session_id}",
    json={"time": "00:00:45"}
)

# 4. Get preview
preview_url = f"http://localhost:8000/preview/{session_id}"

# 5. Finalize video
final_response = requests.post(f"http://localhost:8000/finalize/{session_id}")
'''
    print(python_example)
    
    print("\n🌐 JavaScript/Fetch Example:")
    js_example = '''
// 1. Upload video
const formData = new FormData();
formData.append('file', videoFile);

const uploadResponse = await fetch('/upload/video', {
    method: 'POST',
    body: formData
});
const { session_id } = await uploadResponse.json();

// 2. Trim video
const trimResponse = await fetch(`/trim/${session_id}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        start_time: "00:00:15",
        end_time: "00:02:00"
    })
});

// 3. Get preview
const previewUrl = `/preview/${session_id}`;
videoElement.src = previewUrl;

// 4. WebSocket for real-time editing
const ws = new WebSocket(`ws://localhost:8000/ws/edit/${session_id}`);
ws.send("trim the video from 30 seconds to 2 minutes");
'''
    print(js_example)
    
    print("\n📋 cURL Examples:")
    curl_examples = [
        "# Upload video",
        "curl -X POST http://localhost:8000/upload/video \\",
        "  -F 'file=@video.mp4'",
        "",
        "# Trim video (replace SESSION_ID)",
        "curl -X POST http://localhost:8000/trim/SESSION_ID \\",
        "  -H 'Content-Type: application/json' \\",
        "  -d '{\"start_time\": \"00:00:30\", \"end_time\": \"00:01:45\"}'",
        "",
        "# Generate thumbnail",
        "curl -X POST http://localhost:8000/thumbnail/SESSION_ID \\",
        "  -H 'Content-Type: application/json' \\",
        "  -d '{\"time\": \"00:00:45\"}'",
        "",
        "# Get preview video",
        "curl http://localhost:8000/preview/SESSION_ID -o preview.mp4",
        "",
        "# Finalize video",
        "curl -X POST http://localhost:8000/finalize/SESSION_ID"
    ]
    for line in curl_examples:
        print(line)
    
    print("\n=== Phase 3 Implementation Status ===")
    status_items = [
        "✅ Advanced video editing functions added to utils.py",
        "✅ Phase 3 API endpoints implemented in backend/api.py",
        "✅ Request/Response models for video operations",
        "✅ Session-based video editing with preview support",
        "✅ File serving for thumbnails and processed videos",
        "✅ Real-time preview generation and serving",
        "✅ Video finalization with applied edits",
        "✅ WebSocket support for real-time command processing",
        "✅ Comprehensive error handling and validation",
        "✅ Automatic session cleanup and file management"
    ]
    
    for item in status_items:
        print(item)
    
    print("\n🚀 Ready to Start:")
    print("1. Run: python backend/api.py")
    print("2. Open browser to: http://localhost:8000/docs (FastAPI automatic docs)")
    print("3. Upload a video and start editing!")
    
    return True


if __name__ == "__main__":
    asyncio.run(demo_phase3_api_usage())
    print("\n✨ Phase 3 API is ready for production use!")
