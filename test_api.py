#!/usr/bin/env python3
"""Test script to verify the OpenAI-compatible API endpoint works."""

import requests
import json

# API Configuration
BASE_URL = "https://cloud.infini-ai.com/maas/v1/chat/completions"
API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")
MODEL = "glm-4.6"

def test_api():
    """Test the OpenAI-compatible API endpoint."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Hello! Can you respond with 'API test successful'?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

    print(f"Testing API endpoint: {BASE_URL}")
    print(f"Model: {MODEL}")
    print(f"Request payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...")

    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=30)

        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            response_data = response.json()
            print(f"\nResponse Data: {json.dumps(response_data, indent=2)}")
            print("\n✅ API test successful!")
            return True
        else:
            print(f"\n❌ API test failed!")
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"\n❌ API test failed with exception!")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_api()
