# ElevenLabs API Proxy Integration

This document describes the ElevenLabs API integration in the InfiniProxy server.

## Overview

The proxy server now supports proxying requests to ElevenLabs API for:
- Text-to-Speech (TTS) with REST and streaming
- Text-to-Speech WebSocket for real-time streaming
- Speech-to-Text (STT) with file upload
- Speech-to-Text WebSocket for real-time transcription

## Configuration

Add the following environment variables to configure ElevenLabs integration:

```bash
# Required
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional (defaults shown)
ELEVENLABS_BASE_URL=https://api.elevenlabs.io/v1
ELEVENLABS_WS_URL=wss://api.elevenlabs.io/v1
```

## Available Endpoints

### 1. Text-to-Speech (REST)

**Endpoint:** `POST /v1/elevenlabs/text-to-speech`

**Authentication:** Bearer token (user API key)

**Request Body:**
```json
{
  "text": "Text to convert to speech",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",  // Optional, defaults to Rachel
  "model_id": "eleven_monolingual_v1",  // Optional
  "voice_settings": {  // Optional
    "stability": 0.5,
    "similarity_boost": 0.5
  }
}
```

**Response:** Audio file (audio/mpeg)

**Example:**
```bash
curl -X POST http://localhost:8000/v1/elevenlabs/text-to-speech \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test!"}' \
  --output speech.mp3
```

### 2. Text-to-Speech Streaming (REST)

**Endpoint:** `POST /v1/elevenlabs/text-to-speech/stream`

**Authentication:** Bearer token (user API key)

**Request Body:** Same as regular TTS endpoint

**Response:** Streaming audio (audio/mpeg)

**Example:**
```bash
curl -X POST http://localhost:8000/v1/elevenlabs/text-to-speech/stream \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, streaming test!"}' \
  --output speech_stream.mp3
```

### 3. Text-to-Speech WebSocket

**Endpoint:** `ws://localhost:8000/v1/elevenlabs/text-to-speech/websocket`

**Query Parameters:**
- `voice_id`: Voice ID (default: 21m00Tcm4TlvDq8ikWAM)
- `api_key`: User API key for authentication (required)

**Send Format (JSON):**
```json
{
  "text": "Text to convert",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.5
  }
}
```

**Receive Format:** Binary audio data chunks

**Example (Python):**
```python
import websockets
import asyncio
import json

async def tts_websocket():
    uri = "ws://localhost:8000/v1/elevenlabs/text-to-speech/websocket?api_key=YOUR_API_KEY"

    async with websockets.connect(uri) as websocket:
        # Send text to convert
        await websocket.send(json.dumps({
            "text": "Hello from WebSocket!"
        }))

        # Receive audio chunks
        while True:
            try:
                audio_chunk = await websocket.recv()
                # Process audio chunk (binary data)
                print(f"Received {len(audio_chunk)} bytes")
            except websockets.exceptions.ConnectionClosed:
                break

asyncio.run(tts_websocket())
```

### 4. Speech-to-Text (REST)

**Endpoint:** `POST /v1/elevenlabs/speech-to-text`

**Authentication:** Bearer token (user API key)

**Request:** Multipart form data
- `audio_file`: Audio file to transcribe (required)
- `model`: Model to use (optional, default: whisper-1)

**Response:**
```json
{
  "text": "Transcribed text here",
  "language": "en",
  "duration": 3.5
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/elevenlabs/speech-to-text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "audio_file=@audio.mp3" \
  -F "model=whisper-1"
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/v1/elevenlabs/speech-to-text"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
files = {"audio_file": open("audio.mp3", "rb")}
data = {"model": "whisper-1"}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### 5. Speech-to-Text WebSocket

**Endpoint:** `ws://localhost:8000/v1/elevenlabs/speech-to-text/websocket`

**Query Parameters:**
- `api_key`: User API key for authentication (required)
- `model`: Model to use (default: whisper-1)

**Send Format:** Binary audio data chunks

**Receive Format (JSON):**
```json
{
  "text": "Partial or complete transcription",
  "is_final": false
}
```

**Example (Python):**
```python
import websockets
import asyncio

async def stt_websocket():
    uri = "ws://localhost:8000/v1/elevenlabs/speech-to-text/websocket?api_key=YOUR_API_KEY"

    async with websockets.connect(uri) as websocket:
        # Send audio chunks
        with open("audio.mp3", "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                await websocket.send(chunk)

        # Receive transcriptions
        while True:
            try:
                message = await websocket.recv()
                result = json.loads(message)
                print(f"Transcription: {result['text']}")
                if result.get('is_final'):
                    break
            except websockets.exceptions.ConnectionClosed:
                break

asyncio.run(stt_websocket())
```

## Voice IDs

Common ElevenLabs voice IDs:
- `21m00Tcm4TlvDq8ikWAM` - Rachel (default)
- `AZnzlk1XvdvUeBnXmlld` - Domi
- `EXAVITQu4vr4xnSDxMaL` - Bella
- `ErXwobaYiN019PkySvjV` - Antoni
- `MF3mGyEYCl7XYWbV9V6O` - Elli
- `TxGEqnHWrfWFTfGW9XjX` - Josh
- `VR6AewLTigWG4xSOukaG` - Arnold
- `pNInz6obpgDQGcFmaJgB` - Adam
- `yoZ06aMxZJJ28mfd3POQ` - Sam

You can list all available voices using the ElevenLabs API directly or through their dashboard.

## Usage Tracking

All ElevenLabs API calls are tracked in the usage database with:
- **TTS endpoints:** Input tokens = text length, output tokens = 0
- **STT endpoints:** Input tokens = 0, output tokens = transcription length
- **Model names:**
  - `elevenlabs-tts` - Regular TTS
  - `elevenlabs-tts-stream` - Streaming TTS
  - `elevenlabs-tts-ws` - WebSocket TTS
  - `elevenlabs-stt` - Regular STT
  - `elevenlabs-stt-ws` - WebSocket STT

## Error Handling

All endpoints return appropriate HTTP status codes:
- `400` - Bad request (missing required parameters)
- `401` - Unauthorized (invalid API key)
- `503` - Service unavailable (ElevenLabs API key not configured)
- `500` - Internal server error

Error responses include detailed error messages in JSON format.

## Rate Limiting

Rate limiting is handled by ElevenLabs API. The proxy passes through all rate limit responses.

## WebSocket Authentication

WebSocket endpoints require the user API key to be passed as a query parameter:
```
ws://localhost:8000/v1/elevenlabs/text-to-speech/websocket?api_key=YOUR_API_KEY
```

This is necessary because WebSocket connections don't support Authorization headers in the initial handshake.

## Dependencies

The ElevenLabs integration requires the following Python packages:
- `websockets` - For WebSocket client connections

Install with:
```bash
pip install websockets
```

Or if using the project requirements:
```bash
pip install -r requirements.txt
```

## Testing

### Test TTS (REST)
```bash
export API_KEY="your_proxy_api_key"

curl -X POST http://localhost:8000/v1/elevenlabs/text-to-speech \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing one two three"}' \
  --output test_tts.mp3

# Play the audio
# macOS: afplay test_tts.mp3
# Linux: mpg123 test_tts.mp3
```

### Test TTS Streaming
```bash
curl -X POST http://localhost:8000/v1/elevenlabs/text-to-speech/stream \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Testing streaming"}' \
  --output test_stream.mp3
```

### Test STT (REST)
```bash
# First create a test audio file with TTS
curl -X POST http://localhost:8000/v1/elevenlabs/text-to-speech \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "The quick brown fox jumps over the lazy dog"}' \
  --output test_audio.mp3

# Then transcribe it
curl -X POST http://localhost:8000/v1/elevenlabs/speech-to-text \
  -H "Authorization: Bearer $API_KEY" \
  -F "audio_file=@test_audio.mp3"
```

## Architecture

The proxy acts as a middleware between clients and ElevenLabs API:

```
Client → InfiniProxy → ElevenLabs API
         ↓
    User Authentication
    Usage Tracking
    Logging
```

**Benefits:**
1. Unified API key management
2. Usage tracking and analytics
3. Access control per user
4. Centralized logging
5. Rate limiting per user (can be added)
6. Cost tracking per user

## Security Notes

1. The ElevenLabs API key is stored server-side and never exposed to clients
2. Clients authenticate with their proxy API keys
3. WebSocket connections validate API keys on connection
4. All requests are logged for audit purposes
5. API keys should be stored securely in environment variables or secrets management

## Troubleshooting

### "ElevenLabs API key not configured"
Ensure `ELEVENLABS_API_KEY` environment variable is set.

### WebSocket connection fails
1. Check that API key is passed as query parameter
2. Verify the ElevenLabs WebSocket URL is correct
3. Check firewall/proxy settings for WebSocket support

### Audio quality issues
Adjust `voice_settings`:
```json
{
  "stability": 0.5,      // 0-1, higher = more consistent
  "similarity_boost": 0.75  // 0-1, higher = closer to original voice
}
```

### Transcription accuracy issues
- Ensure audio file is clear and not too noisy
- Try different audio formats (MP3, WAV, M4A)
- Consider using a different model if available

## Future Enhancements

Possible improvements:
1. Add voice cloning endpoints
2. Add history/pronunciation endpoints
3. Implement client-side rate limiting
4. Add audio format conversion
5. Cache frequently used TTS results
6. Add support for SSML (Speech Synthesis Markup Language)
7. Add voice style/emotion controls
8. Implement batch processing endpoints
