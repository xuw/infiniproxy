#!/usr/bin/env python3
"""
Test script for ElevenLabs TTS WebSocket endpoint.

Tests real-time text-to-speech streaming via WebSocket.
"""

import asyncio
import json
import os
import sys
import websockets

# Configuration
API_KEY = "sk-c8c5cc28a0bdc06b1de7de952f9bb3e05df74b5a40d1737c7bbe3d3f90f2f789"
PROXY_WS_URL = "ws://localhost:8000/v1/elevenlabs/text-to-speech/websocket"
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice


async def test_tts_websocket():
    """Test TTS WebSocket endpoint."""
    print("=" * 80)
    print("TESTING ELEVENLABS TTS WEBSOCKET")
    print("=" * 80)

    # Build WebSocket URL with query parameters
    ws_url = f"{PROXY_WS_URL}?voice_id={VOICE_ID}&api_key={API_KEY}"

    print(f"\n🔌 Connecting to: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected!")

            # Test 1: Send simple text
            test_text = "Hello, this is a WebSocket test."
            message = {
                "text": test_text,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            print(f"\n📤 Sending text: '{test_text}'")
            await websocket.send(json.dumps(message))
            print("✅ Message sent")

            # Send EOS (End of Sequence) signal - empty string
            print("\n📤 Sending EOS signal...")
            eos_message = {"text": ""}
            await websocket.send(json.dumps(eos_message))
            print("✅ EOS sent")

            # Receive audio chunks
            print("\n📥 Receiving audio chunks...")
            audio_chunks = []
            chunk_count = 0

            try:
                # Set a timeout for receiving data
                async with asyncio.timeout(15):
                    while True:
                        response = await websocket.recv()

                        if isinstance(response, bytes):
                            # Raw binary audio data
                            chunk_count += 1
                            audio_chunks.append(response)
                            print(f"   Received binary chunk {chunk_count}: {len(response)} bytes")
                        else:
                            # JSON message
                            data = json.loads(response)

                            # Extract base64-encoded audio if present
                            if data.get("audio"):
                                import base64
                                audio_bytes = base64.b64decode(data["audio"])
                                chunk_count += 1
                                audio_chunks.append(audio_bytes)
                                print(f"   Received audio chunk {chunk_count}: {len(audio_bytes)} bytes (base64)")

                            # Check if stream is done
                            if data.get("isFinal"):
                                print(f"   ✅ Stream complete (isFinal=true)")
                                break

            except asyncio.TimeoutError:
                print(f"\n⏱️  Timeout reached after receiving {chunk_count} chunks")
            except websockets.exceptions.ConnectionClosed:
                print(f"\n🔌 Connection closed by server after {chunk_count} chunks")

            # Save audio if we received any
            if audio_chunks:
                total_bytes = sum(len(chunk) for chunk in audio_chunks)
                print(f"\n💾 Total audio received: {total_bytes:,} bytes in {chunk_count} chunks")

                output_file = "/tmp/test_tts_websocket.mp3"
                with open(output_file, "wb") as f:
                    for chunk in audio_chunks:
                        f.write(chunk)
                print(f"✅ Audio saved to: {output_file}")

            else:
                print("\n❌ No audio chunks received")
                return False

            print("\n" + "=" * 80)
            print("✅ TTS WEBSOCKET TEST PASSED")
            print("=" * 80)
            return True

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ Connection failed with status {e.status_code}")
        print(f"   Response: {e.response}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_tts_websocket())
    sys.exit(0 if result else 1)
