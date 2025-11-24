#!/usr/bin/env python3
"""Test WebSocket connection after CORS fix."""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8080/ws/validation_updates"
    print(f"Testing WebSocket connection to {uri}...")
    print("(Server must be restarted for fix to take effect)")
    print()

    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            print("SUCCESS: WebSocket connected!")
            print()

            # Wait for initial connection message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                data = json.loads(message)
                print(f"Received initial message:")
                print(json.dumps(data, indent=2))

                if data.get("type") == "connection_established":
                    print()
                    print("SUCCESS: WebSocket is fully operational!")
                    return True
            except asyncio.TimeoutError:
                print("Warning: No initial message received, but connection is open")
                return True

    except websockets.exceptions.InvalidStatus as e:
        if "403" in str(e):
            print("FAILED: Still getting 403 Forbidden")
            print("Did you restart the server?")
        else:
            print(f"FAILED: {e}")
        return False
    except ConnectionRefusedError:
        print("FAILED: Connection refused - server not running?")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_websocket())
    exit(0 if result else 1)
