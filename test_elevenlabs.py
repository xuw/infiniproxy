#!/usr/bin/env python3
"""
Test script for ElevenLabs API proxy endpoints.

Usage:
    export TEST_API_KEY=your_proxy_api_key
    python test_elevenlabs.py
"""

import os
import requests
import sys

# Configuration
BASE_URL = os.getenv("PROXY_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("TEST_API_KEY")

if not API_KEY:
    print("Error: TEST_API_KEY environment variable not set")
    print("Usage: export TEST_API_KEY=your_proxy_api_key")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def test_tts_rest():
    """Test text-to-speech REST endpoint"""
    print("\n" + "=" * 80)
    print("Testing Text-to-Speech (REST)")
    print("=" * 80)

    url = f"{BASE_URL}/v1/elevenlabs/text-to-speech"
    payload = {
        "text": "Hello! This is a test of the ElevenLabs text-to-speech proxy.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel voice
        "model_id": "eleven_monolingual_v1"
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()

        # Save audio file
        output_file = "test_tts_output.mp3"
        with open(output_file, "wb") as f:
            f.write(response.content)

        print(f"✅ TTS REST test passed")
        print(f"   Audio size: {len(response.content)} bytes")
        print(f"   Saved to: {output_file}")
        print(f"   Play with: afplay {output_file} (macOS) or mpg123 {output_file} (Linux)")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ TTS REST test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ TTS REST test failed: {str(e)}")
        return False


def test_tts_streaming():
    """Test text-to-speech streaming endpoint"""
    print("\n" + "=" * 80)
    print("Testing Text-to-Speech Streaming")
    print("=" * 80)

    url = f"{BASE_URL}/v1/elevenlabs/text-to-speech/stream"
    payload = {
        "text": "This is a streaming test. The audio should be generated in real-time.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM"
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, stream=True, timeout=30)
        response.raise_for_status()

        # Collect streaming chunks
        output_file = "test_tts_stream_output.mp3"
        total_bytes = 0

        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)
                    print(f"   Received {len(chunk)} bytes (total: {total_bytes})", end="\r")

        print(f"\n✅ TTS Streaming test passed")
        print(f"   Total audio size: {total_bytes} bytes")
        print(f"   Saved to: {output_file}")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ TTS Streaming test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ TTS Streaming test failed: {str(e)}")
        return False


def test_stt_rest():
    """Test speech-to-text REST endpoint"""
    print("\n" + "=" * 80)
    print("Testing Speech-to-Text (REST)")
    print("=" * 80)

    # First, create a test audio file using TTS
    print("   Creating test audio file...")
    tts_url = f"{BASE_URL}/v1/elevenlabs/text-to-speech"
    tts_payload = {
        "text": "The quick brown fox jumps over the lazy dog.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM"
    }

    try:
        tts_response = requests.post(tts_url, headers=HEADERS, json=tts_payload, timeout=30)
        tts_response.raise_for_status()

        test_audio_file = "test_stt_input.mp3"
        with open(test_audio_file, "wb") as f:
            f.write(tts_response.content)

        print(f"   Test audio created: {test_audio_file}")

        # Now transcribe it
        print("   Transcribing audio...")
        stt_url = f"{BASE_URL}/v1/elevenlabs/speech-to-text"
        stt_headers = {"Authorization": f"Bearer {API_KEY}"}

        with open(test_audio_file, "rb") as audio_file:
            files = {"audio_file": audio_file}
            data = {"model": "whisper-1"}

            stt_response = requests.post(stt_url, headers=stt_headers, files=files, data=data, timeout=30)
            stt_response.raise_for_status()

            result = stt_response.json()
            transcribed_text = result.get("text", "")

            print(f"✅ STT REST test passed")
            print(f"   Original text: 'The quick brown fox jumps over the lazy dog.'")
            print(f"   Transcribed text: '{transcribed_text}'")
            print(f"   Match: {transcribed_text.lower() == 'the quick brown fox jumps over the lazy dog.'}")

            return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ STT REST test failed: HTTP {e.response.status_code}")
        if e.response is not None:
            print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ STT REST test failed: {str(e)}")
        return False


def test_root_endpoint():
    """Test that ElevenLabs endpoints are listed in root"""
    print("\n" + "=" * 80)
    print("Testing Root Endpoint")
    print("=" * 80)

    url = f"{BASE_URL}/"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        endpoints = data.get("endpoints", {})

        required_endpoints = [
            "elevenlabs_tts",
            "elevenlabs_tts_stream",
            "elevenlabs_tts_ws",
            "elevenlabs_stt",
            "elevenlabs_stt_ws"
        ]

        all_present = all(ep in endpoints for ep in required_endpoints)

        if all_present:
            print(f"✅ Root endpoint test passed")
            print(f"   All ElevenLabs endpoints are listed:")
            for ep in required_endpoints:
                print(f"   - {ep}: {endpoints[ep]}")
            return True
        else:
            print(f"❌ Root endpoint test failed")
            print(f"   Missing endpoints:")
            for ep in required_endpoints:
                if ep not in endpoints:
                    print(f"   - {ep}")
            return False

    except Exception as e:
        print(f"❌ Root endpoint test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 80)
    print("ElevenLabs API Proxy Test Suite")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

    results = []

    # Test root endpoint
    results.append(("Root Endpoint", test_root_endpoint()))

    # Test TTS REST
    results.append(("TTS REST", test_tts_rest()))

    # Test TTS Streaming
    results.append(("TTS Streaming", test_tts_streaming()))

    # Test STT REST (requires ElevenLabs API key to be configured)
    results.append(("STT REST", test_stt_rest()))

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
