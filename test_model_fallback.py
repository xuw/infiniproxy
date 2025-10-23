#!/usr/bin/env python3
"""Test model fallback logic - client-specified model with automatic fallback."""

import requests
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_URL = "https://aiapi.iiis.co:9443"


def load_api_key():
    """Load API key from .env file."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('API_KEY') or os.getenv('ANTHROPIC_API_KEY')
    return api_key


def test_invalid_model_fallback():
    """Test that invalid model falls back to default/key-specific model."""
    api_key = load_api_key()
    if not api_key:
        print("❌ No API key found in .env file")
        return False

    print("="*80)
    print("Testing Model Fallback Logic")
    print("="*80)
    print()

    # Test 1: Client specifies invalid model (should fallback)
    print("📝 Test 1: Client specifies invalid model")
    print(f"   Request: model='invalid-model-xyz'")
    print(f"   Expected: Fallback to default/key-specific model")
    print()

    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "invalid-model-xyz",
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "max_tokens": 10
            },
            verify=False,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            actual_model = data.get("model", "unknown")
            print(f"✅ Test 1 PASSED: Request succeeded with model fallback")
            print(f"   Response model: {actual_model}")
            print(f"   Content: {data.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')[:50]}...")
        else:
            print(f"❌ Test 1 FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Test 1 FAILED with exception: {e}")
        return False

    print()

    # Test 2: Client specifies valid model (should use it)
    print("📝 Test 2: Client specifies valid model")
    print(f"   Request: model='glm-4.6'")
    print(f"   Expected: Use specified model")
    print()

    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "glm-4.6",
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "max_tokens": 10
            },
            verify=False,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            actual_model = data.get("model", "unknown")
            print(f"✅ Test 2 PASSED: Request succeeded")
            print(f"   Response model: {actual_model}")
            print(f"   Content: {data.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')[:50]}...")
        else:
            print(f"❌ Test 2 FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Test 2 FAILED with exception: {e}")
        return False

    print()

    # Test 3: Client doesn't specify model (should use key-specific or default)
    print("📝 Test 3: Client doesn't specify model")
    print(f"   Request: no model field")
    print(f"   Expected: Use key-specific or global default")
    print()

    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "max_tokens": 10
            },
            verify=False,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            actual_model = data.get("model", "unknown")
            print(f"✅ Test 3 PASSED: Request succeeded")
            print(f"   Response model: {actual_model}")
            print(f"   Content: {data.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')[:50]}...")
        else:
            print(f"❌ Test 3 FAILED: Expected 200, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Test 3 FAILED with exception: {e}")
        return False

    print()
    print("="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)
    return True


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_invalid_model_fallback()
    exit(0 if success else 1)
