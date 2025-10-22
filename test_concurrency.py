#!/usr/bin/env python3
"""Test script for concurrent request handling."""

import asyncio
import httpx
import time
import sys
from typing import List, Dict, Any

# Configuration
BASE_URL = "https://aiapi.iiis.co:9443"
API_KEY = "your-api-key"  # Will be read from existing test
CONCURRENT_REQUESTS = 50  # Start with 50, can scale to 200+
LARGE_REQUEST_SIZE = 10000  # Characters in test message


async def make_request(client: httpx.AsyncClient, request_id: int, large: bool = False) -> Dict[str, Any]:
    """Make a single API request."""
    start_time = time.time()

    if large:
        # Large request for testing blocking behavior
        message = "Explain in detail: " + "test " * LARGE_REQUEST_SIZE
    else:
        # Small request for concurrent testing
        message = f"Test request {request_id}: say 'ok'"

    try:
        response = await client.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": message}],
                "max_tokens": 100 if not large else 1000
            },
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=60.0
        )

        elapsed = time.time() - start_time

        return {
            "request_id": request_id,
            "status": response.status_code,
            "success": response.status_code == 200,
            "elapsed": elapsed,
            "large": large
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "request_id": request_id,
            "status": 0,
            "success": False,
            "elapsed": elapsed,
            "error": str(e),
            "large": large
        }


async def check_health(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Check health endpoint."""
    start_time = time.time()
    try:
        response = await client.get(f"{BASE_URL}/health", timeout=5.0)
        elapsed = time.time() - start_time
        return {
            "success": response.status_code == 200,
            "elapsed": elapsed,
            "status": response.status_code
        }
    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "elapsed": elapsed,
            "error": str(e)
        }


async def test_concurrent_requests(num_requests: int, use_large: bool = False):
    """Test concurrent request handling."""
    print(f"\n{'='*80}")
    print(f"Testing {num_requests} concurrent {'LARGE' if use_large else 'small'} requests")
    print(f"{'='*80}")

    # Create async client with high connection limits
    async with httpx.AsyncClient(
        verify=False,
        limits=httpx.Limits(max_keepalive_connections=250, max_connections=300)
    ) as client:
        # Create tasks
        tasks = [
            make_request(client, i, large=use_large)
            for i in range(num_requests)
        ]

        # Run concurrently
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_elapsed = time.time() - start_time

        # Analyze results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        failed = num_requests - successful

        if successful > 0:
            avg_time = sum(r.get("elapsed", 0) for r in results if isinstance(r, dict)) / len(results)
            min_time = min(r.get("elapsed", 0) for r in results if isinstance(r, dict))
            max_time = max(r.get("elapsed", 0) for r in results if isinstance(r, dict))
        else:
            avg_time = min_time = max_time = 0

        print(f"\n✅ Results:")
        print(f"  Total requests: {num_requests}")
        print(f"  Successful: {successful} ({successful/num_requests*100:.1f}%)")
        print(f"  Failed: {failed} ({failed/num_requests*100:.1f}%)")
        print(f"  Total time: {total_elapsed:.2f}s")
        print(f"  Avg response time: {avg_time:.2f}s")
        print(f"  Min response time: {min_time:.2f}s")
        print(f"  Max response time: {max_time:.2f}s")
        print(f"  Requests/second: {num_requests/total_elapsed:.2f}")

        # Show errors if any
        errors = [r.get("error") for r in results if isinstance(r, dict) and not r.get("success")]
        if errors:
            print(f"\n❌ Errors encountered:")
            for error in set(errors):
                count = errors.count(error)
                print(f"  - {error} ({count} times)")

        return successful == num_requests


async def test_health_during_load():
    """Test that health endpoint remains responsive during load."""
    print(f"\n{'='*80}")
    print("Testing health endpoint responsiveness during load")
    print(f"{'='*80}")

    async with httpx.AsyncClient(
        verify=False,
        limits=httpx.Limits(max_keepalive_connections=250, max_connections=300)
    ) as client:
        # Start background large requests
        large_request_tasks = [
            make_request(client, i, large=True)
            for i in range(5)  # 5 large concurrent requests
        ]
        large_request_future = asyncio.gather(*large_request_tasks)

        # Give large requests time to start
        await asyncio.sleep(0.5)

        # Check health endpoint multiple times during load
        health_checks = []
        for i in range(10):
            health_result = await check_health(client)
            health_checks.append(health_result)
            await asyncio.sleep(0.2)  # Check every 200ms

        # Wait for large requests to complete
        await large_request_future

        # Analyze health checks
        successful_health = sum(1 for h in health_checks if h.get("success"))
        avg_health_time = sum(h.get("elapsed", 0) for h in health_checks) / len(health_checks)
        max_health_time = max(h.get("elapsed", 0) for h in health_checks)

        print(f"\n✅ Health Endpoint Results:")
        print(f"  Total health checks: {len(health_checks)}")
        print(f"  Successful: {successful_health} ({successful_health/len(health_checks)*100:.1f}%)")
        print(f"  Avg response time: {avg_health_time:.2f}s")
        print(f"  Max response time: {max_health_time:.2f}s")

        if successful_health == len(health_checks) and max_health_time < 1.0:
            print(f"  ✅ PASS: Health endpoint remained responsive during load")
            return True
        else:
            print(f"  ❌ FAIL: Health endpoint had issues during load")
            return False


async def main():
    """Run all tests."""
    global API_KEY

    # Try to read API key from test file
    try:
        import test_api
        # Get API key from test file or use environment
        import os
        API_KEY = os.getenv("TEST_API_KEY", "test-api-key")
    except:
        print("⚠️  Warning: Could not load API key from test file")
        print("Please set TEST_API_KEY environment variable or update this script")
        return

    print(f"\n{'='*80}")
    print("🚀 InfiniProxy Concurrency Test Suite")
    print(f"{'='*80}")
    print(f"Base URL: {BASE_URL}")
    print(f"Testing async httpx implementation with {CONCURRENT_REQUESTS} concurrent requests")

    # Test 1: Small concurrent requests
    test1_passed = await test_concurrent_requests(CONCURRENT_REQUESTS, use_large=False)

    # Test 2: Health endpoint during load
    test2_passed = await test_health_during_load()

    # Test 3: Scale to 100 concurrent requests
    test3_passed = await test_concurrent_requests(100, use_large=False)

    # Test 4: Scale to 200 concurrent requests
    test4_passed = await test_concurrent_requests(200, use_large=False)

    # Summary
    print(f"\n{'='*80}")
    print("📊 Test Summary")
    print(f"{'='*80}")
    print(f"  Test 1 - {CONCURRENT_REQUESTS} concurrent requests: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"  Test 2 - Health during load: {'✅ PASS' if test2_passed else '❌ FAIL'}")
    print(f"  Test 3 - 100 concurrent requests: {'✅ PASS' if test3_passed else '❌ FAIL'}")
    print(f"  Test 4 - 200 concurrent requests: {'✅ PASS' if test4_passed else '❌ FAIL'}")

    all_passed = test1_passed and test2_passed and test3_passed and test4_passed

    if all_passed:
        print(f"\n✅ ALL TESTS PASSED - Application supports 200+ concurrent requests!")
        print(f"✅ Health endpoint remains responsive during load")
        return 0
    else:
        print(f"\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
