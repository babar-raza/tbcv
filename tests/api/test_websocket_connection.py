#!/usr/bin/env python3
"""Test WebSocket connection to validation_updates endpoint."""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8080/ws/validation_updates"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print("✓ Connected successfully!")

            # Wait for initial messages
            print("\nWaiting for messages (10 seconds)...")
            try:
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"Received: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("No messages received (timeout)")

            print("\n✓ WebSocket connection is working!")

    except websockets.exceptions.WebSocketException as e:
        print(f"✗ WebSocket error: {e}")
    except ConnectionRefusedError:
        print("✗ Connection refused - is the server running?")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
