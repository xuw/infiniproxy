#!/usr/bin/env python3
"""
Test script for SerpAPI proxy endpoints.

Usage:
    export TEST_API_KEY=your_proxy_api_key
    python test_serpapi.py
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
    "Authorization": f"Bearer {API_KEY}"
}


def test_serpapi_search():
    """Test SerpAPI Google Search endpoint"""
    print("\n" + "=" * 80)
    print("Testing SerpAPI Google Search")
    print("=" * 80)

    url = f"{BASE_URL}/v1/serpapi/search"
    params = {
        "q": "artificial intelligence",
        "num": 5,
        "gl": "us",
        "hl": "en"
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ SerpAPI Search test passed")
        print(f"   Query: {params['q']}")
        print(f"   Search ID: {result.get('search_metadata', {}).get('id', 'N/A')}")

        organic_results = result.get('organic_results', [])
        print(f"   Results found: {len(organic_results)}")

        if organic_results:
            print(f"\n   Top 3 results:")
            for i, item in enumerate(organic_results[:3], 1):
                print(f"   {i}. {item.get('title', 'N/A')}")
                print(f"      {item.get('link', 'N/A')}")
                print(f"      {item.get('snippet', 'N/A')[:80]}...")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ SerpAPI Search test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ SerpAPI Search test failed: {str(e)}")
        return False


def test_serpapi_images():
    """Test SerpAPI Google Images endpoint"""
    print("\n" + "=" * 80)
    print("Testing SerpAPI Google Images")
    print("=" * 80)

    url = f"{BASE_URL}/v1/serpapi/images"
    params = {
        "q": "sunset beach",
        "num": 5
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ SerpAPI Images test passed")
        print(f"   Query: {params['q']}")
        print(f"   Search ID: {result.get('search_metadata', {}).get('id', 'N/A')}")

        images_results = result.get('images_results', [])
        print(f"   Images found: {len(images_results)}")

        if images_results:
            print(f"\n   Sample images:")
            for i, img in enumerate(images_results[:3], 1):
                print(f"   {i}. {img.get('title', 'N/A')}")
                print(f"      Thumbnail: {img.get('thumbnail', 'N/A')[:60]}...")
                print(f"      Source: {img.get('source', 'N/A')}")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ SerpAPI Images test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ SerpAPI Images test failed: {str(e)}")
        return False


def test_serpapi_news():
    """Test SerpAPI Google News endpoint"""
    print("\n" + "=" * 80)
    print("Testing SerpAPI Google News")
    print("=" * 80)

    url = f"{BASE_URL}/v1/serpapi/news"
    params = {
        "q": "technology",
        "num": 5,
        "gl": "us"
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ SerpAPI News test passed")
        print(f"   Query: {params['q']}")
        print(f"   Search ID: {result.get('search_metadata', {}).get('id', 'N/A')}")

        news_results = result.get('news_results', [])
        print(f"   News articles found: {len(news_results)}")

        if news_results:
            print(f"\n   Latest articles:")
            for i, article in enumerate(news_results[:3], 1):
                print(f"   {i}. {article.get('title', 'N/A')}")
                print(f"      Source: {article.get('source', 'N/A')}")
                print(f"      Date: {article.get('date', 'N/A')}")
                print(f"      {article.get('snippet', 'N/A')[:60]}...")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ SerpAPI News test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ SerpAPI News test failed: {str(e)}")
        return False


def test_serpapi_shopping():
    """Test SerpAPI Google Shopping endpoint"""
    print("\n" + "=" * 80)
    print("Testing SerpAPI Google Shopping")
    print("=" * 80)

    url = f"{BASE_URL}/v1/serpapi/shopping"
    params = {
        "q": "laptop",
        "num": 5,
        "gl": "us"
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ SerpAPI Shopping test passed")
        print(f"   Query: {params['q']}")
        print(f"   Search ID: {result.get('search_metadata', {}).get('id', 'N/A')}")

        shopping_results = result.get('shopping_results', [])
        print(f"   Products found: {len(shopping_results)}")

        if shopping_results:
            print(f"\n   Sample products:")
            for i, product in enumerate(shopping_results[:3], 1):
                print(f"   {i}. {product.get('title', 'N/A')}")
                print(f"      Price: {product.get('price', 'N/A')}")
                rating = product.get('rating', 'N/A')
                reviews = product.get('reviews', 0)
                print(f"      Rating: {rating} ({reviews} reviews)")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ SerpAPI Shopping test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ SerpAPI Shopping test failed: {str(e)}")
        return False


def test_serpapi_maps():
    """Test SerpAPI Google Maps endpoint"""
    print("\n" + "=" * 80)
    print("Testing SerpAPI Google Maps")
    print("=" * 80)

    url = f"{BASE_URL}/v1/serpapi/maps"
    params = {
        "q": "coffee shops",
        "location": "San Francisco, CA",
        "num": 5
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()

        result = response.json()

        print(f"✅ SerpAPI Maps test passed")
        print(f"   Query: {params['q']}")
        print(f"   Location: {params['location']}")
        print(f"   Search ID: {result.get('search_metadata', {}).get('id', 'N/A')}")

        local_results = result.get('local_results', [])
        print(f"   Places found: {len(local_results)}")

        if local_results:
            print(f"\n   Sample places:")
            for i, place in enumerate(local_results[:3], 1):
                print(f"   {i}. {place.get('title', 'N/A')}")
                rating = place.get('rating', 'N/A')
                reviews = place.get('reviews', 0)
                print(f"      Rating: {rating} ({reviews} reviews)")
                print(f"      Address: {place.get('address', 'N/A')}")
                print(f"      Phone: {place.get('phone', 'N/A')}")

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ SerpAPI Maps test failed: HTTP {e.response.status_code}")
        print(f"   Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ SerpAPI Maps test failed: {str(e)}")
        return False


def test_root_endpoint():
    """Test that SerpAPI endpoints are listed in root"""
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
            "serpapi_search",
            "serpapi_images",
            "serpapi_news",
            "serpapi_shopping",
            "serpapi_maps"
        ]

        all_present = all(ep in endpoints for ep in required_endpoints)

        if all_present:
            print(f"✅ Root endpoint test passed")
            print(f"   All SerpAPI endpoints are listed:")
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
    print("SerpAPI Proxy Test Suite")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}...{API_KEY[-4:]}")

    results = []

    # Test root endpoint
    results.append(("Root Endpoint", test_root_endpoint()))

    # Test SerpAPI Search
    results.append(("SerpAPI Search", test_serpapi_search()))

    # Test SerpAPI Images
    results.append(("SerpAPI Images", test_serpapi_images()))

    # Test SerpAPI News
    results.append(("SerpAPI News", test_serpapi_news()))

    # Test SerpAPI Shopping
    results.append(("SerpAPI Shopping", test_serpapi_shopping()))

    # Test SerpAPI Maps
    results.append(("SerpAPI Maps", test_serpapi_maps()))

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
