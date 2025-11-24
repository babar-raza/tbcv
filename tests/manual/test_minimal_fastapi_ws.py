#!/usr/bin/env python3
"""Test absolute minimal FastAPI WebSocket to isolate the issue."""

from fastapi import FastAPI, WebSocket
import uvicorn

app = FastAPI()

@app.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    """Minimal WebSocket endpoint."""
    print(f"WebSocket connection attempt from {websocket.client}")
    await websocket.accept()
    print("WebSocket accepted!")
    await websocket.send_text("Hello from minimal FastAPI!")
    await websocket.close()
    print("WebSocket closed")

if __name__ == "__main__":
    print("Starting minimal FastAPI server on port 8587...")
    uvicorn.run(app, host="127.0.0.1", port=8587, log_level="debug")
