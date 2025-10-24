#!/usr/bin/env python3
"""Test script for admin user deletion and generate-and-send-key features."""

import requests
import json
import os

BASE_URL = "https://aiapi.iiis.co:9443"

def login_admin():
    """Login as admin and return session cookie."""
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "changeme")

    response = requests.post(
        f"{BASE_URL}/admin/login",
        json={"username": admin_user, "password": admin_password},
        verify=False
    )

    if response.status_code == 200:
        data = response.json()
        print("✅ Admin login successful")
        return data.get("session")
    else:
        print(f"❌ Admin login failed: {response.status_code}")
        print(response.text)
        return None

def list_users(session):
    """List all users."""
    response = requests.get(
        f"{BASE_URL}/admin/users",
        cookies={"admin_session": session},
        verify=False
    )

    if response.status_code == 200:
        users = response.json()
        print(f"\n📋 Total users: {len(users)}")
        for user in users:
            print(f"   - ID: {user['id']}, Username: {user['username']}, Email: {user.get('email', 'N/A')}")
        return users
    else:
        print(f"❌ Failed to list users: {response.status_code}")
        return []

def create_test_user(session):
    """Create a test user for deletion test."""
    response = requests.post(
        f"{BASE_URL}/admin/users",
        cookies={"admin_session": session},
        json={
            "username": f"test_delete_user",
            "email": "weixu@tsinghua.edu.cn",
            "rate_limit": 100
        },
        verify=False
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Test user created: ID={data['user_id']}, Username={data['username']}")
        return data['user_id']
    else:
        print(f"❌ Failed to create test user: {response.status_code}")
        print(response.text)
        return None

def test_generate_and_send_key(session, user_id):
    """Test generate and send key endpoint."""
    print(f"\n🧪 Testing generate-and-send-key for user {user_id}...")

    response = requests.post(
        f"{BASE_URL}/admin/users/{user_id}/generate-and-send-key",
        cookies={"admin_session": session},
        verify=False
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Generate and send key successful!")
        print(f"   - API Key: {data['api_key'][:20]}...")
        print(f"   - Email sent: {data['email_sent']}")
        print(f"   - Email: {data['email']}")
        print(f"   - Message: {data['message']}")
        return True
    else:
        print(f"❌ Generate and send key failed: {response.status_code}")
        print(response.text)
        return False

def test_delete_user(session, user_id):
    """Test user deletion endpoint."""
    print(f"\n🧪 Testing user deletion for user {user_id}...")

    response = requests.delete(
        f"{BASE_URL}/admin/users/{user_id}",
        cookies={"admin_session": session},
        verify=False
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ User deletion successful!")
        print(f"   - Message: {data['message']}")
        return True
    else:
        print(f"❌ User deletion failed: {response.status_code}")
        print(response.text)
        return False

def main():
    """Main test flow."""
    print("🚀 Starting admin features test...\n")

    # Disable SSL warnings for self-signed certificates
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Step 1: Login as admin
    session = login_admin()
    if not session:
        return

    # Step 2: List current users
    print("\n" + "="*50)
    print("BEFORE TEST - Current users:")
    print("="*50)
    users_before = list_users(session)

    # Step 3: Create a test user
    print("\n" + "="*50)
    print("TEST SETUP - Creating test user:")
    print("="*50)
    test_user_id = create_test_user(session)
    if not test_user_id:
        return

    # Step 4: Test generate and send key
    print("\n" + "="*50)
    print("TEST 1 - Generate and Send Key:")
    print("="*50)
    generate_success = test_generate_and_send_key(session, test_user_id)

    # Step 5: List users to verify key creation
    print("\n" + "="*50)
    print("AFTER GENERATE KEY - Current users:")
    print("="*50)
    list_users(session)

    # Step 6: Test user deletion
    print("\n" + "="*50)
    print("TEST 2 - Delete User:")
    print("="*50)
    delete_success = test_delete_user(session, test_user_id)

    # Step 7: List users after deletion
    print("\n" + "="*50)
    print("AFTER DELETION - Current users:")
    print("="*50)
    users_after = list_users(session)

    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY:")
    print("="*50)
    print(f"Generate and Send Key: {'✅ PASS' if generate_success else '❌ FAIL'}")
    print(f"User Deletion: {'✅ PASS' if delete_success else '❌ FAIL'}")
    print(f"Users before: {len(users_before)}, Users after: {len(users_after)}")
    print(f"User count verification: {'✅ PASS' if len(users_after) == len(users_before) else '❌ FAIL'}")
    print("="*50)

if __name__ == "__main__":
    main()
