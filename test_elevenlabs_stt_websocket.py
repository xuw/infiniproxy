#!/usr/bin/env python3
"""
Test script for ElevenLabs STT WebSocket endpoint.

Tests real-time speech-to-text transcription via WebSocket.
"""

import asyncio
import json
import os
import sys
import websockets

# Configuration
API_KEY = "sk-c8c5cc28a0bdc06b1de7de952f9bb3e05df74b5a40d1737c7bbe3d3f90f2f789"
PROXY_WS_URL = "ws://localhost:8000/v1/elevenlabs/speech-to-text/websocket"
MODEL = "whisper-1"


async def test_stt_websocket():
    """Test STT WebSocket endpoint."""
    print("=" * 80)
    print("TESTING ELEVENLABS STT WEBSOCKET")
    print("=" * 80)

    # Check if test audio file exists
    audio_file = "/tmp/test_tts.mp3"
    if not os.path.exists(audio_file):
        print(f"\n❌ Test audio file not found: {audio_file}")
        print("   Please run test_elevenlabs.py first to generate test audio")
        return False

    # Build WebSocket URL with query parameters
    ws_url = f"{PROXY_WS_URL}?api_key={API_KEY}&model={MODEL}"

    print(f"\n🔌 Connecting to: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected!")

            # Read audio file
            with open(audio_file, "rb") as f:
                audio_data = f.read()

            print(f"\n📤 Sending audio data: {len(audio_data):,} bytes")

            # Create tasks for sending and receiving
            async def send_audio():
                """Send audio in chunks."""
                chunk_size = 8192  # 8KB chunks
                chunks_sent = 0

                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i + chunk_size]
                    await websocket.send(chunk)
                    chunks_sent += 1
                    await asyncio.sleep(0.1)  # Small delay between chunks

                print(f"✅ Sent {chunks_sent} audio chunks")

            async def receive_transcriptions():
                """Receive transcription results."""
                transcriptions = []

                try:
                    async with asyncio.timeout(15):
                        while True:
                            response = await websocket.recv()

                            if isinstance(response, str):
                                # JSON transcription
                                result = json.loads(response)
                                text = result.get("text", "")
                                is_final = result.get("is_final", False)

                                status = "✅ FINAL" if is_final else "📝 Partial"
                                print(f"   {status}: '{text}'")

                                transcriptions.append({
                                    "text": text,
                                    "is_final": is_final
                                })

                                if is_final:
                                    break
                            else:
                                print(f"   Received binary data: {len(response)} bytes")

                except asyncio.TimeoutError:
                    print(f"\n⏱️  Timeout reached")

                return transcriptions

            # Run send and receive concurrently
            print("\n📥 Receiving transcriptions...")
            send_task = asyncio.create_task(send_audio())
            receive_task = asyncio.create_task(receive_transcriptions())

            # Wait for receiving to complete
            transcriptions = await receive_task
            await send_task  # Ensure sending completes

            # Display results
            print("\n" + "=" * 80)
            print("📊 TRANSCRIPTION RESULTS")
            print("=" * 80)

            if transcriptions:
                final_transcriptions = [t for t in transcriptions if t["is_final"]]
                if final_transcriptions:
                    print(f"\n✅ Final transcription: '{final_transcriptions[-1]['text']}'")
                    print(f"   Total responses: {len(transcriptions)}")
                    print(f"   Final responses: {len(final_transcriptions)}")
                else:
                    print(f"\n⚠️  Received {len(transcriptions)} partial transcriptions, but no final result")
            else:
                print("\n❌ No transcriptions received")
                return False

            print("\n" + "=" * 80)
            print("✅ STT WEBSOCKET TEST PASSED")
            print("=" * 80)
            return True

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"\n❌ Connection failed with status {e.status_code}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_stt_websocket())
    sys.exit(0 if result else 1)
