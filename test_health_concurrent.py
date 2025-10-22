#!/usr/bin/env python3
"""Simple test to verify health endpoint remains responsive."""

import asyncio
import httpx
import time

BASE_URL = "https://aiapi.iiis.co:9443"


async def check_health():
    """Check health endpoint once."""
    start = time.time()
    try:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(f"{BASE_URL}/health", timeout=5.0)
            elapsed = time.time() - start
            return {
                "success": response.status_code == 200,
                "elapsed": elapsed,
                "status": response.status_code
            }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "success": False,
            "elapsed": elapsed,
            "error": str(e)
        }


async def concurrent_health_checks(num_checks: int):
    """Run multiple concurrent health checks."""
    print(f"\nRunning {num_checks} concurrent health checks...")
    start = time.time()

    tasks = [check_health() for _ in range(num_checks)]
    results = await asyncio.gather(*tasks)

    total_time = time.time() - start
    successful = sum(1 for r in results if r["success"])
    avg_time = sum(r["elapsed"] for r in results) / len(results)
    max_time = max(r["elapsed"] for r in results)

    print(f"Results:")
    print(f"  Total checks: {num_checks}")
    print(f"  Successful: {successful} ({successful/num_checks*100:.1f}%)")
    print(f"  Failed: {num_checks - successful}")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Avg response: {avg_time:.3f}s")
    print(f"  Max response: {max_time:.3f}s")
    print(f"  Checks/sec: {num_checks/total_time:.1f}")

    return successful == num_checks


async def main():
    """Run health check tests."""
    print("="*80)
    print("Health Endpoint Concurrency Test")
    print("="*80)

    # Test 1: 50 concurrent health checks
    test1 = await concurrent_health_checks(50)

    # Test 2: 100 concurrent health checks
    test2 = await concurrent_health_checks(100)

    # Test 3: 200 concurrent health checks
    test3 = await concurrent_health_checks(200)

    # Test 4: 300 concurrent health checks
    test4 = await concurrent_health_checks(300)

    print("\n" + "="*80)
    print("Summary:")
    print(f"  50 concurrent:  {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"  100 concurrent: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"  200 concurrent: {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"  300 concurrent: {'✅ PASS' if test4 else '❌ FAIL'}")

    if test1 and test2 and test3 and test4:
        print("\n✅ All tests passed! Health endpoint supports 300+ concurrent requests.")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
