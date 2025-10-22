#!/usr/bin/env python3
"""Test admin session persistence across multiple requests."""

import requests
import time

BASE_URL = "https://aiapi.iiis.co:9443"

def test_admin_session_persistence():
    """Test that admin sessions persist across multiple requests."""
    print("="*80)
    print("Testing Admin Session Persistence")
    print("="*80)

    # Step 1: Login
    print("\n1. Logging in as admin...")
    login_response = requests.post(
        f"{BASE_URL}/admin/login",
        json={"username": "admin", "password": "changeme"},
        verify=False
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False

    # Extract session cookie
    session_cookie = login_response.cookies.get('admin_session')
    if not session_cookie:
        print("❌ No session cookie received")
        return False

    print(f"✅ Login successful, session token: {session_cookie[:20]}...")

    # Step 2: Make multiple requests with the session cookie
    print("\n2. Testing session persistence with 20 requests...")
    cookies = {'admin_session': session_cookie}

    success_count = 0
    for i in range(20):
        response = requests.get(
            f"{BASE_URL}/admin/users",
            cookies=cookies,
            verify=False
        )

        if response.status_code == 200:
            success_count += 1
            print(f"  Request {i+1}/20: ✅ Status {response.status_code}")
        else:
            print(f"  Request {i+1}/20: ❌ Status {response.status_code} - {response.text}")

        # Small delay between requests
        time.sleep(0.1)

    print(f"\n3. Results: {success_count}/20 requests succeeded")

    # Step 3: Verify session still works after some time
    print("\n4. Waiting 5 seconds and testing again...")
    time.sleep(5)

    response = requests.get(
        f"{BASE_URL}/admin/users",
        cookies=cookies,
        verify=False
    )

    if response.status_code == 200:
        print("✅ Session still valid after delay")
    else:
        print(f"❌ Session invalid after delay: {response.status_code}")
        return False

    # Step 4: Logout
    print("\n5. Testing logout...")
    logout_response = requests.post(
        f"{BASE_URL}/admin/logout",
        cookies=cookies,
        verify=False
    )

    if logout_response.status_code == 200:
        print("✅ Logout successful")
    else:
        print(f"❌ Logout failed: {logout_response.status_code}")

    # Step 5: Verify session is invalidated
    print("\n6. Verifying session is invalidated after logout...")
    response = requests.get(
        f"{BASE_URL}/admin/users",
        cookies=cookies,
        verify=False
    )

    if response.status_code == 401:
        print("✅ Session properly invalidated after logout")
    else:
        print(f"❌ Session still valid after logout (expected 401, got {response.status_code})")
        return False

    print("\n" + "="*80)
    if success_count == 20:
        print("✅ ALL TESTS PASSED")
        print("✅ Admin sessions persist across multiple requests")
        print("✅ Sessions work correctly with multi-worker deployment")
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({success_count}/20 succeeded)")
        return False

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    success = test_admin_session_persistence()
    exit(0 if success else 1)
