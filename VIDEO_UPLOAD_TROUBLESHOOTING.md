# Video Upload Troubleshooting Guide
## "Failed to upload video" Error Resolution

### 🎯 Issue Resolved: CORS Configuration

The upload failure was caused by **CORS (Cross-Origin Resource Sharing) configuration** that was too restrictive. The backend was only allowing connections from `http://localhost:3000` but the frontend was connecting from different origins.

### ✅ **Solution Implemented**

Updated `backend/api.py` with comprehensive CORS configuration:

```python
# Allow multiple origins for development and testing
allowed_origins = [
    FRONTEND_ORIGIN,
    "http://localhost:3000",
    "http://127.0.0.1:3000", 
    "http://localhost:5173",  # Vite dev server default
    "http://127.0.0.1:5173",
    "http://localhost:8000",  # Backend itself for testing
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 🧪 **Testing Results**

#### Backend API Tests ✅
- **Root endpoint:** Working (`200 OK`)
- **Health check:** Working (`200 OK`)
- **Video upload:** Working (`200 OK`) - Returns session ID and WebSocket token

#### CORS Tests ✅
- **Upload with Origin header:** Working (`200 OK`)
- **CORS methods:** All methods allowed
- **CORS credentials:** Enabled

### 🔧 **Common Upload Issues & Solutions**

#### 1. **CORS Errors** ✅ RESOLVED
**Symptoms:**
- "Failed to upload video" message
- Browser console shows CORS errors
- OPTIONS requests failing

**Solution:** Updated CORS configuration to allow multiple origins

#### 2. **File Type Validation**
**Check:** Ensure your video file has an allowed extension:
```python
ALLOWED_UPLOAD_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv"]
```

#### 3. **File Size Limits**
**Check:** Verify file size is within limits (if configured):
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB default
```

#### 4. **Server Connection**
**Check:** Ensure backend server is running:
```bash
# Start the server
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000

# Test connectivity
curl http://127.0.0.1:8000/health
```

#### 5. **Directory Permissions**
**Check:** Ensure upload directory exists and is writable:
```bash
# Check if temp directory exists
dir C:\my_video_editor\temp

# Create if missing
mkdir C:\my_video_editor\temp
```

### 🧩 **Frontend Configuration**

Ensure your frontend is configured with the correct API endpoint:

```javascript
// Frontend .env file
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### 🚀 **Quick Test Commands**

#### Test Upload Functionality
```bash
# Run the test script
python test_upload.py
```

#### Test CORS Configuration
```bash
# Run CORS test
python test_cors.py
```

#### Start Development Server
```bash
# Backend
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload

# Frontend (if using Vite)
cd frontend && npm run dev
```

### 📊 **Diagnostic Information**

#### Successful Upload Response:
```json
{
  "session_id": "uuid-here",
  "filename": "video.mp4",
  "ws_token": "websocket-token-here"
}
```

#### Expected Server Logs:
```
INFO: Started server process
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: 127.0.0.1:port - "POST /upload/video HTTP/1.1" 200 OK
```

### 🛠️ **Development Tools**

#### Browser DevTools Check:
1. Open browser DevTools (F12)
2. Check Network tab during upload
3. Look for:
   - CORS errors in Console
   - Failed requests in Network
   - Response codes and headers

#### Server Logs Check:
Monitor server output for:
- Connection attempts
- Error messages
- Request processing status

### 🔄 **Recovery Steps**

If upload still fails after CORS fix:

1. **Restart the backend server**
2. **Clear browser cache**
3. **Check file format compatibility**
4. **Verify network connectivity**
5. **Test with a smaller file**

### 📈 **Performance Notes**

- **File size:** Larger files take longer to upload
- **Network:** Slow connections may timeout
- **Format:** Some formats may require conversion
- **Browser:** Different browsers may have different limits

### 🎉 **Success Confirmation**

When upload is working correctly, you should see:
- ✅ Network request shows `200 OK`
- ✅ Response contains `session_id`
- ✅ No CORS errors in console
- ✅ Server logs show successful upload

---

**Status:** ✅ **RESOLVED** - Video upload functionality is now working correctly with proper CORS configuration.

The backend API is fully functional and ready for frontend integration.
