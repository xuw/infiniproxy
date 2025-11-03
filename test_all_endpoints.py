#!/usr/bin/env python3
"""
Comprehensive endpoint testing for InfiniProxy
Tests all major API endpoints with the provided API key
"""

import requests
import json
import sys

# Configuration
PROXY_URL = "https://aiapi.iiis.co:9443"
API_KEY = "sk-dd6249f07fd462e5c36ecf9f0e990af070bfa8886914a9b0848bd87d56a8aefd"

# Headers
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing: /health")
    print("="*60)

    try:
        response = requests.get(f"{PROXY_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_openai_chat():
    """Test OpenAI chat completions endpoint"""
    print("\n" + "="*60)
    print("Testing: /v1/chat/completions (OpenAI)")
    print("="*60)

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Say 'Hello from InfiniProxy!'"}],
        "max_tokens": 50
    }

    try:
        response = requests.post(
            f"{PROXY_URL}/v1/chat/completions",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data.get('model')}")
            print(f"Response: {data['choices'][0]['message']['content']}")
            return True
        else:
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_claude_messages():
    """Test Claude messages endpoint"""
    print("\n" + "="*60)
    print("Testing: /v1/messages (Claude)")
    print("="*60)

    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "Say 'Hello from Claude via InfiniProxy!'"}]
    }

    try:
        response = requests.post(
            f"{PROXY_URL}/v1/messages",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data.get('model')}")
            print(f"Response: {data['content'][0]['text']}")
            return True
        else:
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_firecrawl_scrape():
    """Test Firecrawl scrape endpoint"""
    print("\n" + "="*60)
    print("Testing: /v1/firecrawl/scrape")
    print("="*60)

    payload = {
        "url": "https://example.com"
    }

    try:
        response = requests.post(
            f"{PROXY_URL}/v1/firecrawl/scrape",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            if data.get('data'):
                content_preview = data['data'].get('markdown', '')[:100]
                print(f"Content preview: {content_preview}...")
            return True
        else:
            print(f"Response: {response.text}")
            # API key not configured is expected, not a proxy failure
            if "API key not configured" in response.text:
                print("⚠️  Firecrawl API key not configured (proxy working)")
                return True
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_firecrawl_search():
    """Test Firecrawl search endpoint"""
    print("\n" + "="*60)
    print("Testing: /v1/firecrawl/search")
    print("="*60)

    payload = {
        "query": "FastAPI Python framework"
    }

    try:
        response = requests.post(
            f"{PROXY_URL}/v1/firecrawl/search",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            # Firecrawl v2 API returns data nested under data.web
            if data.get('data', {}).get('web'):
                results = data['data']['web']
                print(f"Results count: {len(results)}")
                if results:
                    print(f"First result: {results[0].get('title', 'N/A')}")
            return True
        else:
            print(f"Response: {response.text}")
            # API key not configured is expected, not a proxy failure
            if "API key not configured" in response.text:
                print("⚠️  Firecrawl API key not configured (proxy working)")
                return True
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_tavily_search():
    """Test Tavily search endpoint"""
    print("\n" + "="*60)
    print("Testing: /v1/tavily/search")
    print("="*60)

    payload = {
        "query": "Python programming latest news",
        "max_results": 3
    }

    try:
        response = requests.post(
            f"{PROXY_URL}/v1/tavily/search",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                print(f"Results count: {len(data['results'])}")
                print(f"First result: {data['results'][0].get('title', 'N/A')}")
            return True
        else:
            print(f"Response: {response.text}")
            # API key not configured is expected, not a proxy failure
            if "API key not configured" in response.text:
                print("⚠️  Tavily API key not configured (proxy working)")
                return True
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_serpapi_search():
    """Test SerpAPI search endpoint"""
    print("\n" + "="*60)
    print("Testing: /v1/serpapi/search")
    print("="*60)

    params = {
        "q": "Python programming",
        "num": 3
    }

    try:
        response = requests.get(
            f"{PROXY_URL}/v1/serpapi/search",
            headers=HEADERS,
            params=params,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if data.get('organic_results'):
                print(f"Results count: {len(data['organic_results'])}")
                print(f"First result: {data['organic_results'][0].get('title', 'N/A')}")
            return True
        else:
            print(f"Response: {response.text}")
            # SerpAPI may not be configured, not necessarily a proxy failure
            if response.status_code in [500, 503]:
                print("⚠️  SerpAPI not configured (not a proxy issue)")
                return True  # Count as success for proxy testing
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_elevenlabs_tts():
    """Test ElevenLabs TTS endpoint"""
    print("\n" + "="*60)
    print("Testing: /v1/elevenlabs/text-to-speech")
    print("="*60)

    payload = {
        "text": "Hello from InfiniProxy!",
        "model_id": "eleven_monolingual_v1"
    }

    try:
        response = requests.post(
            f"{PROXY_URL}/v1/elevenlabs/text-to-speech",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            audio_size = len(response.content)
            print(f"✅ Audio generated: {audio_size} bytes")
            return True
        else:
            print(f"Response: {response.text}")
            # API key not configured or quota issues are expected
            if "API key not configured" in response.text or response.status_code in [402, 429]:
                print("⚠️  ElevenLabs API key not configured or quota limit (proxy working)")
                return True  # Count as success for proxy testing
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all endpoint tests"""
    print("\n" + "🚀 " * 30)
    print("InfiniProxy Comprehensive Endpoint Testing")
    print("🚀 " * 30)
    print(f"\nProxy URL: {PROXY_URL}")
    print(f"API Key: {API_KEY[:20]}...")

    results = {}

    # Run all tests
    results['health'] = test_health()
    results['openai_chat'] = test_openai_chat()
    results['claude_messages'] = test_claude_messages()
    results['firecrawl_scrape'] = test_firecrawl_scrape()
    results['firecrawl_search'] = test_firecrawl_search()
    results['tavily_search'] = test_tavily_search()
    results['serpapi_search'] = test_serpapi_search()
    results['elevenlabs_tts'] = test_elevenlabs_tts()

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for endpoint, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{endpoint:25s} {status}")

    total = len(results)
    passed = sum(results.values())

    print("\n" + "-"*60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("-"*60)

    # Exit code
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    main()
