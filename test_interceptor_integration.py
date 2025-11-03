#!/usr/bin/env python3
"""
Test InfiniProxy Interceptor with official client libraries

This script tests that official client libraries work with the interceptor
without any code changes - just by setting HTTP_PROXY environment variables.

Prerequisites:
    1. Start the interceptor: python infiniproxy_interceptor.py
    2. Run this test: python test_interceptor_integration.py
"""

import os
import sys
import time
import subprocess

# Configure to use the interceptor proxy
os.environ['HTTP_PROXY'] = 'http://localhost:8888'
os.environ['HTTPS_PROXY'] = 'http://localhost:8888'

# Also set proxy API key for direct API test
os.environ['AIAPI_URL'] = 'https://aiapi.iiis.co:9443'
os.environ['AIAPI_KEY'] = 'sk-dd6249f07fd462e5c36ecf9f0e990af070bfa8886914a9b0848bd87d56a8aefd'

print("=" * 70)
print("InfiniProxy Interceptor Integration Tests")
print("=" * 70)
print(f"\nProxy Configuration:")
print(f"  HTTP_PROXY:  {os.environ['HTTP_PROXY']}")
print(f"  HTTPS_PROXY: {os.environ['HTTPS_PROXY']}")
print(f"\nInfiniProxy Configuration:")
print(f"  URL: {os.environ['AIAPI_URL']}")
print(f"  Key: {os.environ['AIAPI_KEY'][:20]}...")
print("\n" + "=" * 70 + "\n")

test_results = {}


def test_direct_api_through_proxy():
    """Test direct API calls through the proxy"""
    print("\n" + "=" * 70)
    print("TEST 1: Direct API Calls Through Proxy")
    print("=" * 70)

    try:
        import requests

        # Test Tavily search through proxy
        print("  Testing Tavily search...")
        response = requests.post(
            f"{os.environ['AIAPI_URL']}/v1/tavily/search",
            headers={'Authorization': f"Bearer {os.environ['AIAPI_KEY']}"},
            json={'query': 'Python', 'max_results': 3},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tavily search successful")
            print(f"   Results: {len(data.get('results', []))} found")
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_requests_library_direct():
    """Test using requests library to call APIs directly (simulating client behavior)"""
    print("\n" + "=" * 70)
    print("TEST 2: Requests Library Direct API Calls")
    print("=" * 70)

    try:
        import requests

        # Simulate what a client library does - direct call to service domain
        # The interceptor should intercept and redirect this

        print("  Testing direct call to api.tavily.com (should be intercepted)...")

        # This simulates what Tavily client library does internally
        response = requests.post(
            'https://api.tavily.com/search',
            headers={'Content-Type': 'application/json'},
            json={'query': 'Python', 'max_results': 3},
            timeout=30
        )

        print(f"  Response status: {response.status_code}")

        if response.status_code == 200:
            print("✅ Request intercepted and routed successfully")
            return True
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            return False

    except requests.exceptions.ConnectionError as e:
        print(f"⚠️  Connection error (interceptor may not be running): {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_proxy_environment():
    """Test that proxy environment variables are set correctly"""
    print("\n" + "=" * 70)
    print("TEST 3: Proxy Environment Variables")
    print("=" * 70)

    try:
        required_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'AIAPI_URL', 'AIAPI_KEY']
        all_set = True

        for var in required_vars:
            value = os.environ.get(var)
            if value:
                display_value = value[:20] + '...' if len(value) > 20 else value
                print(f"  ✅ {var}: {display_value}")
            else:
                print(f"  ❌ {var}: NOT SET")
                all_set = False

        if all_set:
            print("\n✅ All environment variables configured")
            return True
        else:
            print("\n❌ Some environment variables missing")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_interceptor_running():
    """Test if interceptor is running and accepting connections"""
    print("\n" + "=" * 70)
    print("TEST 4: Interceptor Server Status")
    print("=" * 70)

    try:
        import socket

        # Try to connect to the proxy port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        result = sock.connect_ex(('localhost', 8888))
        sock.close()

        if result == 0:
            print("✅ Interceptor is running on localhost:8888")
            return True
        else:
            print("❌ Interceptor is not running on localhost:8888")
            print("   Start it with: python infiniproxy_interceptor.py")
            return False

    except Exception as e:
        print(f"❌ Error checking interceptor: {e}")
        return False


def test_wrapper_client_comparison():
    """Compare direct wrapper client vs interceptor proxy"""
    print("\n" + "=" * 70)
    print("TEST 5: Wrapper Client vs Interceptor Comparison")
    print("=" * 70)

    try:
        # Import wrapper client
        from infiniproxy_clients import TavilyClient

        # Test 1: Wrapper client (no proxy)
        print("  Testing wrapper client (direct to InfiniProxy)...")
        # Temporarily remove proxy settings
        http_proxy = os.environ.pop('HTTP_PROXY', None)
        https_proxy = os.environ.pop('HTTPS_PROXY', None)

        client = TavilyClient()
        results1 = client.search("Python", max_results=3)

        # Restore proxy settings
        if http_proxy:
            os.environ['HTTP_PROXY'] = http_proxy
        if https_proxy:
            os.environ['HTTPS_PROXY'] = https_proxy

        if results1:
            print(f"  ✅ Wrapper client works: {len(results1.get('results', []))} results")
        else:
            print("  ⚠️  Wrapper client returned no results")

        # Test 2: Direct API call through interceptor
        print("  Testing direct API through interceptor...")
        import requests

        response = requests.post(
            f"{os.environ['AIAPI_URL']}/v1/tavily/search",
            headers={'Authorization': f"Bearer {os.environ['AIAPI_KEY']}"},
            json={'query': 'Python', 'max_results': 3},
            timeout=30
        )

        results2 = response.json() if response.status_code == 200 else None

        if results2:
            print(f"  ✅ Interceptor works: {len(results2.get('results', []))} results")
        else:
            print("  ⚠️  Interceptor returned no results")

        # Both should work
        if results1 and results2:
            print("\n✅ Both methods work successfully")
            return True
        else:
            print("\n⚠️  One or both methods failed")
            return False

    except ImportError:
        print("⚠️  infiniproxy_clients not available, skipping comparison")
        return True  # Not a failure, just skipped
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""

    # Check if interceptor is running first
    if not test_interceptor_running():
        print("\n" + "=" * 70)
        print("⚠️  INTERCEPTOR NOT RUNNING")
        print("=" * 70)
        print("\nPlease start the interceptor in another terminal:")
        print("  python infiniproxy_interceptor.py")
        print("\nThen run this test again.")
        sys.exit(1)

    # Run tests
    test_results['environment'] = test_proxy_environment()
    test_results['direct_api'] = test_direct_api_through_proxy()
    test_results['requests_direct'] = test_requests_library_direct()
    test_results['wrapper_comparison'] = test_wrapper_client_comparison()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in test_results.values() if r)
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25s} {status}")

    print("\n" + "=" * 70)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    print("=" * 70)

    # Usage notes
    print("\n" + "=" * 70)
    print("USAGE WITH OFFICIAL CLIENTS")
    print("=" * 70)
    print("""
The interceptor allows you to use official client libraries with ZERO
code changes. Just set the proxy environment variables:

# In your terminal:
export HTTP_PROXY=http://localhost:8888
export HTTPS_PROXY=http://localhost:8888

# Or in Python:
import os
os.environ['HTTP_PROXY'] = 'http://localhost:8888'
os.environ['HTTPS_PROXY'] = 'http://localhost:8888'

# Now use official clients normally:
from tavily import TavilyClient
client = TavilyClient(api_key="dummy")  # API key from interceptor
results = client.search("query")

# The interceptor automatically:
# 1. Intercepts requests to api.tavily.com
# 2. Redirects to InfiniProxy
# 3. Injects your AIAPI_KEY
# 4. Returns results to client
""")
    print("=" * 70)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
