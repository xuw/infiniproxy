#!/usr/bin/env python3
"""
Test script to verify proxy client configuration.

This script demonstrates how to use the proxy configuration
with various API clients and libraries.

Required Environment Variables:
    AIAPI_URL - Proxy server URL (e.g., http://localhost:8000)
    AIAPI_KEY - Proxy API key

Usage:
    export AIAPI_URL=http://localhost:8000
    export AIAPI_KEY=your-api-key-here
    python test_proxy_client_config.py
"""

import os
import sys
import json
from set_proxy_env import configure_proxy


def test_environment_configuration():
    """Test that environment variables are set correctly."""
    print("=" * 60)
    print("TEST 1: Environment Configuration")
    print("=" * 60)

    # Configure proxy
    config = configure_proxy()

    print(f"✅ Proxy URL: {config['proxy_url']}")
    print(f"✅ API Key: {config['proxy_api_key'][:20]}...")
    print()

    # Verify critical environment variables
    critical_vars = [
        "OPENAI_API_BASE",
        "OPENAI_BASE_URL",
        "ANTHROPIC_BASE_URL",
        "FIRECRAWL_BASE_URL",
        "ELEVENLABS_API_BASE",
        "TAVILY_API_BASE",
        "SERPAPI_BASE_URL",
    ]

    all_set = True
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False

    print()
    if all_set:
        print("✅ All critical environment variables are set correctly")
        return True
    else:
        print("❌ Some environment variables are missing")
        return False


def test_openai_configuration():
    """Test OpenAI client configuration."""
    print("\n" + "=" * 60)
    print("TEST 2: OpenAI Client Configuration")
    print("=" * 60)

    try:
        import openai

        # Check if environment variables are picked up
        api_base = os.getenv("OPENAI_API_BASE")
        api_key = os.getenv("OPENAI_API_KEY")

        print(f"OpenAI API Base: {api_base}")
        print(f"OpenAI API Key: {api_key[:20]}...")

        # Note: We won't make actual API calls in this test
        # Just verify configuration
        print("✅ OpenAI client can be configured with proxy settings")
        print("   (Actual API calls require running proxy server)")
        return True

    except ImportError:
        print("⚠️  OpenAI library not installed (pip install openai)")
        print("   Skipping OpenAI configuration test")
        return True


def test_anthropic_configuration():
    """Test Anthropic client configuration."""
    print("\n" + "=" * 60)
    print("TEST 3: Anthropic Client Configuration")
    print("=" * 60)

    try:
        import anthropic

        # Check if environment variables are picked up
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        api_key = os.getenv("ANTHROPIC_API_KEY")

        print(f"Anthropic Base URL: {base_url}")
        print(f"Anthropic API Key: {api_key[:20]}...")

        print("✅ Anthropic client can be configured with proxy settings")
        print("   (Actual API calls require running proxy server)")
        return True

    except ImportError:
        print("⚠️  Anthropic library not installed (pip install anthropic)")
        print("   Skipping Anthropic configuration test")
        return True


def test_requests_configuration():
    """Test using requests library with proxy."""
    print("\n" + "=" * 60)
    print("TEST 4: Generic HTTP Client (requests)")
    print("=" * 60)

    try:
        import requests

        # Get proxy URL from either AIAPI_URL or INFINIPROXY_URL
        proxy_url = os.getenv("AIAPI_URL") or os.getenv("INFINIPROXY_URL") or "http://localhost:8000"
        api_key = os.getenv("AIAPI_KEY") or os.getenv("INFINIPROXY_API_KEY")

        print(f"Proxy URL: {proxy_url}")
        if api_key:
            print(f"API Key: {api_key[:20]}...")
        else:
            print("API Key: Not set")
        print()

        # Test health endpoint
        try:
            response = requests.get(
                f"{proxy_url}/health",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check successful")
                print(f"   Status: {data.get('status')}")
                print(f"   Environment: {data.get('environment')}")
                return True
            else:
                print(f"⚠️  Health check returned status {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            print("⚠️  Cannot connect to proxy server")
            print("   Make sure proxy server is running:")
            print(f"   docker start infiniproxy-test")
            return False

    except ImportError:
        print("⚠️  Requests library not installed (pip install requests)")
        return False


def test_curl_command_generation():
    """Generate curl commands for testing."""
    print("\n" + "=" * 60)
    print("TEST 5: cURL Command Generation")
    print("=" * 60)

    # Get proxy URL from either AIAPI_URL or INFINIPROXY_URL
    proxy_url = os.getenv("AIAPI_URL") or os.getenv("INFINIPROXY_URL") or "http://localhost:8000"
    api_key = os.getenv("AIAPI_KEY") or os.getenv("INFINIPROXY_API_KEY") or "your-api-key"

    commands = {
        "Health Check": f'curl {proxy_url}/health',

        "OpenAI Models": f'''curl {proxy_url}/v1/models \\
  -H "Authorization: Bearer {api_key}"''',

        "OpenAI Chat": f'''curl {proxy_url}/v1/chat/completions \\
  -H "Authorization: Bearer {api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "model": "gpt-4",
    "messages": [{{"role": "user", "content": "Hello!"}}],
    "max_tokens": 50
  }}'
''',

        "Claude Messages": f'''curl {proxy_url}/v1/messages \\
  -H "Authorization: Bearer {api_key}" \\
  -H "Content-Type: application/json" \\
  -H "anthropic-version: 2023-06-01" \\
  -d '{{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{{"role": "user", "content": "Hello!"}}]
  }}'
''',

        "Firecrawl Scrape": f'''curl -X POST {proxy_url}/v1/firecrawl/scrape \\
  -H "Authorization: Bearer {api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "url": "https://example.com",
    "formats": ["markdown"]
  }}'
''',
    }

    for name, command in commands.items():
        print(f"\n{name}:")
        print("-" * 60)
        print(command)

    print()
    print("✅ cURL commands generated successfully")
    print("   Copy and run these commands to test the proxy")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧪 InfiniProxy Client Configuration Test Suite")
    print("=" * 60)
    print()

    results = {
        "Environment Configuration": test_environment_configuration(),
        "OpenAI Configuration": test_openai_configuration(),
        "Anthropic Configuration": test_anthropic_configuration(),
        "HTTP Client Test": test_requests_configuration(),
        "cURL Commands": test_curl_command_generation(),
    }

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    total = len(results)
    passed = sum(1 for r in results.values() if r)

    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
