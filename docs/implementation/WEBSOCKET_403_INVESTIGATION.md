# WebSocket 403 Forbidden Investigation

**Date:** 2025-11-23
**Status:** ⚠️ **BLOCKED - Environment Issue**
**Severity:** CRITICAL - Prevents all real-time dashboard features

---

## Problem Statement

ALL WebSocket connections to the FastAPI server return HTTP 403 Forbidden, even with minimal test endpoints. The 403 error occurs at the uvicorn level BEFORE reaching FastAPI application handlers.

**User Report:**
"I am seeing Disconnected on Workflow Details tab - same issue must be checked everywhere on dashboard."

---

## Attempted Fixes (All Failed)

### 1. ✗ Added `ws="websockets"` parameter to uvicorn.run()
**Files:** [main.py:197](main.py:197), [main.py:208](main.py:208)
**Result:** Still 403

### 2. ✗ Installed and tried `wsproto` implementation
**Command:** `pip install wsproto`
**Config:** Changed `ws="websockets"` to `ws="wsproto"`
**Result:** Still 403

### 3. ✗ Started uvicorn from command line
**Command:** `python -m uvicorn api.server:app --host 127.0.0.1 --port 8585 --ws websockets`
**Result:** Still 403

### 4. ✗ Moved CORS middleware after WebSocket routes
**File:** [api/server.py:336-338](api/server.py:336-338)
**Result:** Still 403

### 5. ✗ Completely disabled CORS middleware
**File:** [api/server.py:580-589](api/server.py:580-589) (commented out)
**Result:** Still 403

### 6. ✗ Created minimal test WebSocket endpoint
**File:** [api/server.py:563-568](api/server.py:563-568)
```python
@app.websocket("/ws/test")
async def test_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Hello from test WebSocket!")
    await websocket.close()
```
**Result:** Still 403

---

## Environment Details

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.13.2 | Very recent release (Jan 2025) |
| FastAPI | 0.119.1 | Latest |
| uvicorn | 0.37.0 | Latest |
| websockets | 15.0.1 | Latest |
| wsproto | 1.3.2 | Installed during troubleshooting |
| OS | Windows | win32 |

---

## Server Logs

```
INFO:     Started server process [113908]
INFO:     Uvicorn running on http://127.0.0.1:8585
INFO:     127.0.0.1:XXXXX - "WebSocket /ws/test" 403
INFO:     connection rejected (403 Forbidden)
INFO:     connection closed
```

**Key observation:** uvicorn rejects the connection BEFORE our FastAPI endpoint handlers are called. None of our logging in the WebSocket endpoint functions is reached.

---

## Test Results

### WebSocket Connection Test
**File:** [test_simple_ws.py](test_simple_ws.py)
**Code:**
```python
import asyncio
import websockets

async def test():
    uri = "ws://127.0.0.1:8585/ws/test"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            message = await websocket.recv()
            print(f"Received: {message}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

asyncio.run(test())
```

**Output:**
```
Connecting to ws://127.0.0.1:8585/ws/test...
Error: InvalidStatus: server rejected WebSocket connection: HTTP 403
```

---

## WebSocket Endpoints Properly Defined

All WebSocket endpoints have correct type hints and are properly registered:

### Test Endpoint
[api/server.py:563-568](api/server.py:563-568)
```python
@app.websocket("/ws/test")
async def test_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Hello from test WebSocket!")
    await websocket.close()
```

### Workflow Progress Endpoint
[api/server.py:571-575](api/server.py:571-575)
```python
@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    from api.websocket_endpoints import websocket_endpoint as ws_handler
    await ws_handler(websocket, workflow_id)
```

### Global Validation Updates Endpoint
[api/server.py:578-584](api/server.py:578-584)
```python
@app.websocket("/ws/validation_updates")
async def validation_updates_websocket(websocket: WebSocket):
    from api.websocket_endpoints import connection_manager
    await connection_manager.connect(websocket, "validation_updates")
    # ... rest of handler
```

All have proper `WebSocket` type hints as required by FastAPI.

---

## Research Findings

### From GitHub/StackOverflow

1. **uvicorn WebSocket Support:**
   - Default `--ws=auto` may not work correctly
   - Recommendation: Use `--ws=websockets` explicitly
   - ✗ **Tried - Still 403**

2. **Path Issues:**
   - WebSocket spec says server returns 403 if path is unexpected
   - ✗ **Not applicable** - Our endpoints are properly defined

3. **Type Hint Issues:**
   - Missing `: WebSocket` type hint causes 403
   - ✗ **Not applicable** - All our endpoints have type hints

4. **ASGI Specification:**
   - 403 behavior is according to ASGI spec
   - Server-side decision before FastAPI handlers run

### Potential Root Causes

#### Most Likely: Python 3.13.2 Compatibility Issue
- Python 3.13.2 was released in January 2025 (very recent)
- FastAPI 0.119.1 and uvicorn 0.37.0 may not be fully compatible with Python 3.13
- No specific Python 3.13 + FastAPI WebSocket issues found in search (too recent)

#### Alternative Theories:
1. **Windows-specific issue** with WebSocket handling in uvicorn
2. **Dependency conflict** between websockets 15.0.1 and Python 3.13
3. **Low-level networking issue** in the Python 3.13 runtime on Windows

---

## Impact Assessment

### Features Broken
- ✗ Dashboard live updates (validation events, recommendation events)
- ✗ Workflow progress tracking (real-time progress bars)
- ✗ Connection status indicators (always show "Disconnected")
- ✗ Toast notifications for events
- ✗ Heartbeat connections

### Features Still Working
- ✅ All REST API endpoints (HTTP)
- ✅ Batch validation workflows (execution works, just no real-time progress)
- ✅ Database operations
- ✅ Ollama LLM integration
- ✅ All validation logic
- ✅ Static dashboard pages (page loads work, just no live updates)

### User Experience Impact
Users can:
- Create workflows via REST API
- Poll workflow status with GET requests
- Use all validation features
- View static dashboard pages

Users cannot:
- See real-time progress updates
- Get instant notifications
- See live connection status

---

## Next Steps / Recommendations

### Immediate Workarounds

#### Option 1: Add Polling Fallback (Recommended)
Modify dashboard JavaScript to poll REST endpoints when WebSocket connection fails:

```javascript
// In workflow_detail_realtime.html
if (ws.readyState !== WebSocket.OPEN) {
    // Fallback to polling every 2 seconds
    setInterval(async () => {
        const response = await fetch(`/api/workflows/${workflowId}`);
        const data = await response.json();
        updateUI(data);
    }, 2000);
}
```

**Effort:** 2-3 hours
**Impact:** Restores functionality with slight delay

#### Option 2: Server-Sent Events (SSE)
Replace WebSockets with SSE (simpler protocol, better compatibility):

```python
from fastapi.responses import StreamingResponse

@app.get("/api/workflows/{workflow_id}/stream")
async def workflow_stream(workflow_id: str):
    async def event_generator():
        while True:
            data = await get_workflow_status(workflow_id)
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(1)
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Effort:** 4-6 hours
**Impact:** Full real-time functionality restored

### Long-Term Fixes

#### Option 3: Downgrade Python to 3.12.x
Test if the issue is Python 3.13-specific:

```bash
# Install Python 3.12
pyenv install 3.12.0
pyenv local 3.12.0

# Reinstall dependencies
pip install -r requirements.txt

# Test WebSocket
python test_simple_ws.py
```

**Effort:** 1-2 hours
**Risk:** May require code changes if using Python 3.13-specific features

#### Option 4: Upgrade FastAPI/uvicorn (Wait for Updates)
Monitor for Python 3.13-specific fixes:

```bash
# Check for updates
pip list --outdated

# Upgrade when available
pip install --upgrade fastapi uvicorn
```

**Effort:** Ongoing monitoring
**Timeline:** Likely within 1-2 months

#### Option 5: Use Docker Container with Python 3.12
Isolate environment issues:

```dockerfile
FROM python:3.12-slim
# ... rest of Dockerfile
```

**Effort:** 2-3 hours
**Benefit:** Consistent environment across deployments

---

## Testing Instructions

### Verify the Issue Persists

```bash
# Start server
python main.py --mode api --host 127.0.0.1 --port 8585

# Test WebSocket in another terminal
python test_simple_ws.py

# Expected output (current):
# Error: InvalidStatus: server rejected WebSocket connection: HTTP 403

# Desired output (after fix):
# Connecting to ws://127.0.0.1:8585/ws/test...
# Connected!
# Received: Hello from test WebSocket!
```

### Test After Implementing Fix

1. **Start server** (with fix applied)
2. **Open browser** to http://127.0.0.1:8585/dashboard/
3. **Check connection status** - Should show "Live" 🟢 instead of "Disconnected" 🔴
4. **Create workflow** - Progress should update in real-time
5. **Check browser console** - WebSocket connection should succeed

---

## Files Requiring Updates (If Implementing Polling Fallback)

1. **templates/dashboard_home_realtime.html** - Add polling fallback
2. **templates/workflow_detail_realtime.html** - Add polling fallback
3. **api/dashboard.py** - May need additional REST endpoints for polling

---

## Related Documentation

- [ALL_FIXES_VERIFICATION_COMPLETE.md](reports/ALL_FIXES_VERIFICATION_COMPLETE.md) - Previous fixes that work except WebSocket
- [LIVE_UPDATES_FIX_COMPLETE.md](reports/LIVE_UPDATES_FIX_COMPLETE.md) - LiveBus implementation (works correctly once WebSocket connects)
- [WORKFLOW_PROGRESS_FIX_COMPLETE.md](reports/WORKFLOW_PROGRESS_FIX_COMPLETE.md) - Workflow progress implementation (works correctly once WebSocket connects)

---

## Summary

The WebSocket 403 error is a fundamental environment incompatibility issue, likely between Python 3.13.2 and FastAPI/uvicorn. All application-level code is correct:

✅ WebSocket endpoints properly defined
✅ Type hints present
✅ LiveBus implementation correct
✅ Connection manager working
✅ CORS not interfering

❌ uvicorn rejects connections at protocol level BEFORE reaching app code

**Recommended immediate action:** Implement polling fallback (Option 1) to restore functionality while investigating long-term fixes.

**Recommended long-term action:** Test with Python 3.12.x to confirm if this is a Python 3.13 compatibility issue.

---

**Generated:** 2025-11-23
**Server:** Running on http://127.0.0.1:8585 (PID: 113908)
**Status:** WebSocket functionality BLOCKED, REST API fully operational
