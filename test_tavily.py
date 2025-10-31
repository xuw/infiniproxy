#!/usr/bin/env python3
"""
Test script for Tavily proxy endpoints.

Usage:
    export TEST_API_KEY=your_proxy_api_key
    python test_tavily.py
"""

import os
import requests
import sys
import json

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


def test_tavily_search_basic():
    """Test Tavily Search endpoint with basic parameters"""
    print("\n" + "=" * 80)
    print("Testing Tavily Search - Basic")
    print("=" * 80)

    url = f"{BASE_URL}/v1/tavily/search"
    payload = {
        "query": "artificial intelligence 2024",
        "max_results": 5
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ Tavily Search Basic test passed")
        print(f"   Query: {result.get('query')}")
        print(f"   Request ID: {result.get('request_id', 'N/A')}")
        print(f"   Response time: {result.get('response_time', 'N/A')}s")

        results = result.get('results', [])
        print(f"   Results found: {len(results)}")

        if results:
            print(f"\n   Top 3 results:")
            for i, item in enumerate(results[:3], 1):
                print(f"   {i}. {item.get('title', 'N/A')}")
                print(f"      URL: {item.get('url', 'N/A')}")
                print(f"      Score: {item.get('score', 'N/A')}")
                print(f"      {item.get('content', 'N/A')[:80]}...")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ Tavily Search Basic test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Tavily Search Basic test failed: {str(e)}")
        return False


def test_tavily_search_advanced():
    """Test Tavily Search endpoint with advanced parameters"""
    print("\n" + "=" * 80)
    print("Testing Tavily Search - Advanced")
    print("=" * 80)

    url = f"{BASE_URL}/v1/tavily/search"
    payload = {
        "query": "latest developments in quantum computing",
        "search_depth": "advanced",
        "max_results": 5,
        "include_answer": True,
        "include_images": True,
        "time_range": "month"
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()

        print(f"✅ Tavily Search Advanced test passed")
        print(f"   Query: {result.get('query')}")
        print(f"   Request ID: {result.get('request_id', 'N/A')}")

        # Check for answer
        answer = result.get('answer')
        if answer:
            print(f"\n   AI Answer: {answer[:150]}...")

        # Check for images
        images = result.get('images', [])
        if images:
            print(f"\n   Images found: {len(images)}")
            for i, img in enumerate(images[:3], 1):
                if isinstance(img, dict):
                    print(f"   {i}. {img.get('url', 'N/A')[:60]}...")
                else:
                    print(f"   {i}. {str(img)[:60]}...")

        # Check results
        results = result.get('results', [])
        print(f"\n   Search results: {len(results)}")
        if results:
            print(f"   Top result: {results[0].get('title', 'N/A')}")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ Tavily Search Advanced test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Tavily Search Advanced test failed: {str(e)}")
        return False


def test_tavily_search_news():
    """Test Tavily Search endpoint with news topic"""
    print("\n" + "=" * 80)
    print("Testing Tavily Search - News Topic")
    print("=" * 80)

    url = f"{BASE_URL}/v1/tavily/search"
    payload = {
        "query": "technology news",
        "topic": "news",
        "max_results": 5,
        "time_range": "week"
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ Tavily Search News test passed")
        print(f"   Query: {result.get('query')}")

        results = result.get('results', [])
        print(f"   News articles found: {len(results)}")

        if results:
            print(f"\n   Recent news:")
            for i, item in enumerate(results[:3], 1):
                print(f"   {i}. {item.get('title', 'N/A')}")
                print(f"      {item.get('url', 'N/A')}")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ Tavily Search News test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Tavily Search News test failed: {str(e)}")
        return False


def test_tavily_extract_single():
    """Test Tavily Extract endpoint with single URL"""
    print("\n" + "=" * 80)
    print("Testing Tavily Extract - Single URL")
    print("=" * 80)

    url = f"{BASE_URL}/v1/tavily/extract"
    payload = {
        "urls": "https://www.python.org/"
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()

        print(f"✅ Tavily Extract Single test passed")
        print(f"   Request ID: {result.get('request_id', 'N/A')}")
        print(f"   Response time: {result.get('response_time', 'N/A')}s")

        successful = result.get('results', [])
        failed = result.get('failed_results', [])

        print(f"   Successful extractions: {len(successful)}")
        print(f"   Failed extractions: {len(failed)}")

        if successful:
            first = successful[0]
            print(f"\n   URL: {first.get('url')}")
            content = first.get('raw_content', '')
            print(f"   Content length: {len(content)} characters")
            print(f"   Content preview: {content[:100]}...")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ Tavily Extract Single test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Tavily Extract Single test failed: {str(e)}")
        return False


def test_tavily_extract_multiple():
    """Test Tavily Extract endpoint with multiple URLs"""
    print("\n" + "=" * 80)
    print("Testing Tavily Extract - Multiple URLs")
    print("=" * 80)

    url = f"{BASE_URL}/v1/tavily/extract"
    payload = {
        "urls": [
            "https://www.python.org/",
            "https://docs.python.org/3/"
        ],
        "extract_depth": "basic",
        "format": "markdown"
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=90)
        response.raise_for_status()

        result = response.json()

        print(f"✅ Tavily Extract Multiple test passed")
        print(f"   Request ID: {result.get('request_id', 'N/A')}")

        successful = result.get('results', [])
        failed = result.get('failed_results', [])

        print(f"   Successful extractions: {len(successful)}")
        print(f"   Failed extractions: {len(failed)}")

        if successful:
            print(f"\n   Extracted URLs:")
            for i, r in enumerate(successful, 1):
                content_len = len(r.get('raw_content', ''))
                print(f"   {i}. {r.get('url')} ({content_len} chars)")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ Tavily Extract Multiple test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Tavily Extract Multiple test failed: {str(e)}")
        return False


def test_tavily_extract_with_images():
    """Test Tavily Extract endpoint with images"""
    print("\n" + "=" * 80)
    print("Testing Tavily Extract - With Images")
    print("=" * 80)

    url = f"{BASE_URL}/v1/tavily/extract"
    payload = {
        "urls": ["https://www.python.org/"],
        "include_images": True,
        "include_favicon": True
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()

        print(f"✅ Tavily Extract Images test passed")

        successful = result.get('results', [])
        if successful:
            first = successful[0]
            print(f"   URL: {first.get('url')}")

            images = first.get('images', [])
            print(f"   Images found: {len(images)}")
            if images:
                for i, img in enumerate(images[:3], 1):
                    print(f"   {i}. {img[:60]}...")

            favicon = first.get('favicon')
            if favicon:
                print(f"   Favicon: {favicon}")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ Tavily Extract Images test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Tavily Extract Images test failed: {str(e)}")
        return False


def test_root_endpoint():
    """Test that Tavily endpoints are listed in root"""
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
            "tavily_search",
            "tavily_extract"
        ]

        all_present = all(ep in endpoints for ep in required_endpoints)

        if all_present:
            print(f"✅ Root endpoint test passed")
            print(f"   All Tavily endpoints are listed:")
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
    print("Tavily Proxy Test Suite")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

    results = []

    # Test root endpoint
    results.append(("Root Endpoint", test_root_endpoint()))

    # Test Tavily Search
    results.append(("Tavily Search Basic", test_tavily_search_basic()))
    results.append(("Tavily Search Advanced", test_tavily_search_advanced()))
    results.append(("Tavily Search News", test_tavily_search_news()))

    # Test Tavily Extract
    results.append(("Tavily Extract Single", test_tavily_extract_single()))
    results.append(("Tavily Extract Multiple", test_tavily_extract_multiple()))
    results.append(("Tavily Extract Images", test_tavily_extract_with_images()))

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
