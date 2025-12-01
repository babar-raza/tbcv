#!/usr/bin/env python3
"""Test WebSocket connection to debug 403 errors."""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8585/ws/validation_updates"

    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            # Wait for initial message
            message = await websocket.recv()
            print(f"Received: {message}")

            # Send ping
            await websocket.send(json.dumps({"type": "ping"}))
            response = await websocket.recv()
            print(f"Ping response: {response}")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"Connection failed with status code: {e.status_code}")
        print(f"Headers: {e.headers}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
