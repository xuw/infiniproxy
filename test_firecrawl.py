#!/usr/bin/env python3
"""
Test script for Firecrawl API proxy endpoints.

Tests the Firecrawl scrape, crawl, search, and status endpoints locally.
"""

import requests
import json
import time
import os
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("TEST_API_KEY", "your-test-api-key")


def make_request(
    method: str,
    endpoint: str,
    data: Optional[dict] = None,
    headers: Optional[dict] = None
) -> dict:
    """Make an HTTP request to the proxy server."""
    url = f"{BASE_URL}{endpoint}"

    default_headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    if headers:
        default_headers.update(headers)

    print(f"\n{'='*80}")
    print(f"📤 {method.upper()} {endpoint}")
    if data:
        print(f"Request body: {json.dumps(data, indent=2)}")

    try:
        if method.lower() == "get":
            response = requests.get(url, headers=default_headers)
        elif method.lower() == "post":
            response = requests.post(url, headers=default_headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")

        print(f"Status: {response.status_code}")

        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:500]}...")
            return result
        except json.JSONDecodeError:
            print(f"Response (text): {response.text[:500]}...")
            return {"error": "Invalid JSON response", "text": response.text}

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"error": str(e)}
    finally:
        print(f"{'='*80}\n")


def test_health():
    """Test the health endpoint."""
    print("\n🏥 Testing health endpoint...")
    result = make_request("GET", "/health")
    assert "status" in result, "Health check should return status"
    print("✅ Health check passed")


def test_firecrawl_scrape():
    """Test the Firecrawl scrape endpoint."""
    print("\n🔍 Testing Firecrawl scrape endpoint...")

    data = {
        "url": "https://example.com",
        "formats": ["markdown", "html"]
    }

    result = make_request("POST", "/v1/firecrawl/scrape", data=data)

    if "error" in result:
        print(f"⚠️  Scrape test returned error (expected if Firecrawl API key not configured): {result.get('error')}")
    else:
        print("✅ Scrape endpoint responded successfully")

    return result


def test_firecrawl_crawl():
    """Test the Firecrawl crawl endpoint."""
    print("\n🕷️  Testing Firecrawl crawl endpoint...")

    data = {
        "url": "https://example.com",
        "limit": 10,
        "scrapeOptions": {
            "formats": ["markdown"]
        }
    }

    result = make_request("POST", "/v1/firecrawl/crawl", data=data)

    if "error" in result:
        print(f"⚠️  Crawl test returned error (expected if Firecrawl API key not configured): {result.get('error')}")
    else:
        print("✅ Crawl endpoint responded successfully")
        job_id = result.get("id")
        if job_id:
            print(f"📋 Job ID: {job_id}")
            return job_id

    return None


def test_firecrawl_crawl_status(job_id: str):
    """Test the Firecrawl crawl status endpoint."""
    print(f"\n📊 Testing Firecrawl status endpoint for job: {job_id}...")

    result = make_request("GET", f"/v1/firecrawl/crawl/status/{job_id}")

    if "error" in result:
        print(f"⚠️  Status test returned error: {result.get('error')}")
    else:
        print("✅ Status endpoint responded successfully")
        print(f"Status: {result.get('status', 'unknown')}")

    return result


def test_firecrawl_search():
    """Test the Firecrawl search endpoint."""
    print("\n🔎 Testing Firecrawl search endpoint...")

    data = {
        "query": "python web scraping",
        "limit": 5
    }

    result = make_request("POST", "/v1/firecrawl/search", data=data)

    if "error" in result:
        print(f"⚠️  Search test returned error (expected if Firecrawl API key not configured): {result.get('error')}")
    else:
        print("✅ Search endpoint responded successfully")
        num_results = len(result.get("data", []))
        print(f"Results: {num_results} items")

    return result


def test_root_endpoint():
    """Test the root endpoint to verify Firecrawl endpoints are listed."""
    print("\n🏠 Testing root endpoint...")
    result = make_request("GET", "/")

    endpoints = result.get("endpoints", {})
    firecrawl_endpoints = [k for k in endpoints.keys() if k.startswith("firecrawl")]

    print(f"Found {len(firecrawl_endpoints)} Firecrawl endpoints:")
    for endpoint in firecrawl_endpoints:
        print(f"  - {endpoint}: {endpoints[endpoint]}")

    assert len(firecrawl_endpoints) == 4, "Should have 4 Firecrawl endpoints"
    print("✅ Root endpoint shows Firecrawl endpoints")


def main():
    """Run all tests."""
    print("=" * 80)
    print("🚀 Starting Firecrawl Proxy Tests")
    print("=" * 80)

    print(f"\nBase URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}..." if len(API_KEY) > 10 else API_KEY)

    # Check if Firecrawl API key is configured
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")
    if not firecrawl_key:
        print("\n⚠️  WARNING: FIRECRAWL_API_KEY not set in environment")
        print("Some tests may fail. To test with real Firecrawl API:")
        print("  export FIRECRAWL_API_KEY=your-firecrawl-api-key")
    else:
        print(f"\n✅ FIRECRAWL_API_KEY configured: {firecrawl_key[:10]}...")

    # Run tests
    try:
        test_health()
        test_root_endpoint()

        test_firecrawl_scrape()
        test_firecrawl_search()

        # Test crawl and status (if crawl succeeds)
        job_id = test_firecrawl_crawl()
        if job_id:
            # Wait a bit before checking status
            time.sleep(2)
            test_firecrawl_crawl_status(job_id)

        print("\n" + "=" * 80)
        print("✅ All tests completed!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
