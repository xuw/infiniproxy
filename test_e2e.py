#!/usr/bin/env python3
"""End-to-end test for the proxy server with real API."""

import requests
import json
import os

# Load environment variables from .env if present
from dotenv import load_dotenv
load_dotenv()

PROXY_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint."""
    response = requests.get(f"{PROXY_URL}/health")
    print(f"\n✅ Health check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200


def test_simple_message():
    """Test simple message creation."""
    claude_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Say 'Hello from the proxy!' and nothing else."
            }
        ]
    }

    print("\n📤 Sending Claude API request...")
    response = requests.post(
        f"{PROXY_URL}/v1/messages",
        json=claude_request,
        timeout=30
    )

    print(f"✅ Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📥 Claude API Response:")
        print(json.dumps(data, indent=2))

        assert data["type"] == "message"
        assert data["role"] == "assistant"
        assert len(data["content"]) > 0
        assert data["content"][0]["type"] == "text"
        print(f"\n💬 Assistant says: {data['content'][0]['text']}")
    else:
        print(f"\n❌ Error: {response.text}")
        raise AssertionError(f"Request failed with status {response.status_code}")


def test_with_system_message():
    """Test message with system prompt."""
    claude_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 150,
        "system": "You are a helpful math tutor. Always show your reasoning.",
        "messages": [
            {
                "role": "user",
                "content": "What is 15 * 24?"
            }
        ]
    }

    print("\n📤 Sending Claude API request with system message...")
    response = requests.post(
        f"{PROXY_URL}/v1/messages",
        json=claude_request,
        timeout=30
    )

    print(f"✅ Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📥 Claude API Response:")
        print(json.dumps(data, indent=2))

        print(f"\n💬 Assistant says: {data['content'][0]['text']}")
    else:
        print(f"\n❌ Error: {response.text}")
        raise AssertionError(f"Request failed with status {response.status_code}")


if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI to Claude Proxy - End-to-End Tests")
    print("=" * 60)
    print(f"\n⚠️  Make sure the proxy server is running on {PROXY_URL}")
    print("   Run: python proxy_server.py")
    print()

    try:
        test_health()
        test_simple_message()
        test_with_system_message()

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)

    except requests.ConnectionError:
        print("\n❌ Error: Could not connect to proxy server")
        print(f"   Make sure the server is running on {PROXY_URL}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
