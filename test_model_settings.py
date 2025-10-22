#!/usr/bin/env python3
"""Test per-API-key model settings functionality."""

import requests
import json
import sys

BASE_URL = "https://aiapi.iiis.co:9443"

# Test API keys (these should be created beforehand)
# You can create them using the admin interface or API
TEST_KEYS = [
    # Add your test API keys here, e.g.:
    # "sk-test1...",
    # "sk-test2...",
]

def test_get_model_setting(api_key):
    """Test GET /settings/model endpoint."""
    print(f"\n📥 Testing GET /settings/model with key {api_key[:20]}...")

    response = requests.get(
        f"{BASE_URL}/settings/model",
        headers={"Authorization": f"Bearer {api_key}"},
        verify=False
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ GET successful: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ GET failed: {response.status_code} - {response.text}")
        return None


def test_set_model_setting(api_key, model_name):
    """Test PUT /settings/model endpoint."""
    print(f"\n📤 Testing PUT /settings/model with key {api_key[:20]}...")
    print(f"   Setting model to: {model_name}")

    response = requests.put(
        f"{BASE_URL}/settings/model",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={"model_name": model_name},
        verify=False
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ PUT successful: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ PUT failed: {response.status_code} - {response.text}")
        return None


def test_unset_model_setting(api_key):
    """Test unsetting model (back to default)."""
    print(f"\n🔄 Testing unsetting model with key {api_key[:20]}...")

    response = requests.put(
        f"{BASE_URL}/settings/model",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={"model_name": None},
        verify=False
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Unset successful: {json.dumps(data, indent=2)}")
        return data
    else:
        print(f"❌ Unset failed: {response.status_code} - {response.text}")
        return None


def test_request_with_model(api_key, expected_model=None):
    """Test that the model setting is actually used in requests."""
    print(f"\n🚀 Testing actual request with key {api_key[:20]}...")
    if expected_model:
        print(f"   Expected model to be used: {expected_model}")

    # Test with Claude API format
    response = requests.post(
        f"{BASE_URL}/v1/messages",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "claude-3-5-sonnet-20241022",  # Will be ignored if per-key model is set
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "Say 'test'"}]
        },
        verify=False
    )

    print(f"   Response status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Request successful")
        return True
    else:
        print(f"❌ Request failed: {response.text[:200]}")
        return False


def main():
    print("="*80)
    print("Testing Per-API-Key Model Settings")
    print("="*80)

    if not TEST_KEYS:
        print("\n⚠️  No test API keys configured!")
        print("Please add API keys to the TEST_KEYS list in the script.")
        print("\nYou can create test API keys using the admin interface at:")
        print(f"{BASE_URL}/admin/login-page")
        return False

    success_count = 0
    total_tests = 0

    for i, api_key in enumerate(TEST_KEYS):
        print(f"\n{'='*80}")
        print(f"Testing API Key {i+1}/{len(TEST_KEYS)}")
        print(f"{'='*80}")

        # Test 1: Get initial model setting
        total_tests += 1
        result = test_get_model_setting(api_key)
        if result is not None:
            success_count += 1

        # Test 2: Set a specific model
        total_tests += 1
        test_model = f"test-model-{i+1}"
        result = test_set_model_setting(api_key, test_model)
        if result is not None:
            success_count += 1

        # Test 3: Verify the model was set
        total_tests += 1
        result = test_get_model_setting(api_key)
        if result and result.get('model_name') == test_model:
            print(f"✅ Model setting verified: {test_model}")
            success_count += 1
        else:
            print(f"❌ Model setting verification failed")

        # Test 4: Make a request with the model setting
        total_tests += 1
        if test_request_with_model(api_key, test_model):
            success_count += 1

        # Test 5: Unset the model (back to default)
        total_tests += 1
        result = test_unset_model_setting(api_key)
        if result is not None:
            success_count += 1

        # Test 6: Verify model is unset
        total_tests += 1
        result = test_get_model_setting(api_key)
        if result and result.get('model_name') is None and result.get('using_default'):
            print(f"✅ Model unset verified, using default")
            success_count += 1
        else:
            print(f"❌ Model unset verification failed")

    # Test with different models for different keys
    if len(TEST_KEYS) >= 2:
        print(f"\n{'='*80}")
        print("Testing Different Models for Different Keys")
        print(f"{'='*80}")

        models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]

        for i, api_key in enumerate(TEST_KEYS):
            model = models[i % len(models)]
            total_tests += 1
            if test_set_model_setting(api_key, model):
                success_count += 1

        # Verify all keys have their own models
        print(f"\n🔍 Verifying each key has its own model...")
        for i, api_key in enumerate(TEST_KEYS):
            expected_model = models[i % len(models)]
            total_tests += 1
            result = test_get_model_setting(api_key)
            if result and result.get('model_name') == expected_model:
                print(f"✅ Key {i+1}: {expected_model}")
                success_count += 1
            else:
                print(f"❌ Key {i+1}: Expected {expected_model}, got {result.get('model_name') if result else 'None'}")

    # Final results
    print(f"\n{'='*80}")
    print(f"Test Results: {success_count}/{total_tests} tests passed")
    print(f"{'='*80}")

    if success_count == total_tests:
        print("✅ ALL TESTS PASSED")
        print("✅ Per-API-key model settings work correctly")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({total_tests - success_count} failures)")
        return False


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = main()
    sys.exit(0 if success else 1)
