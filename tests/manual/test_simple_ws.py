#!/usr/bin/env python3
"""Test simple WebSocket endpoint."""
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
