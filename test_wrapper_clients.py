#!/usr/bin/env python3
"""
Test InfiniProxy wrapper clients for compatibility and functionality
"""

import os
import sys

# Set proxy configuration
os.environ["AIAPI_URL"] = "https://aiapi.iiis.co:9443"
os.environ["AIAPI_KEY"] = "sk-dd6249f07fd462e5c36ecf9f0e990af070bfa8886914a9b0848bd87d56a8aefd"

from infiniproxy_clients import (
    ElevenLabsClient,
    SerpAPIClient,
    FirecrawlClient,
    TavilyClient,
    ProxyClientError,
    create_elevenlabs_client,
    get_tavily_client
)

print("=" * 70)
print("InfiniProxy Wrapper Clients Test Suite")
print("=" * 70)
print(f"\nProxy URL: {os.environ['AIAPI_URL']}")
print(f"API Key: {os.environ['AIAPI_KEY'][:20]}...")
print("\n" + "=" * 70 + "\n")

test_results = {}


def test_elevenlabs_wrapper():
    """Test ElevenLabs wrapper client"""
    print("\n" + "=" * 70)
    print("TEST 1: ElevenLabs Wrapper Client")
    print("=" * 70)

    try:
        # Test initialization
        client = ElevenLabsClient()
        print("✓ Client initialized successfully")

        # Test text-to-speech
        print("  Testing text-to-speech generation...")
        audio = client.text_to_speech(
            text="Hello from InfiniProxy!",
            model_id="eleven_monolingual_v1"
        )

        if audio and len(audio) > 0:
            print(f"✓ Generated audio: {len(audio)} bytes")
            return True
        else:
            print("⚠️  Generated audio is empty")
            return False

    except ProxyClientError as e:
        print(f"⚠️  Proxy error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_serpapi_wrapper():
    """Test SerpAPI wrapper client"""
    print("\n" + "=" * 70)
    print("TEST 2: SerpAPI Wrapper Client")
    print("=" * 70)

    try:
        # Test initialization
        client = SerpAPIClient()
        print("✓ Client initialized successfully")

        # Test search
        print("  Testing search...")
        results = client.search(query="Python programming", num=3)

        if results and isinstance(results, dict):
            print(f"✓ Search successful")
            print(f"  Results keys: {', '.join(results.keys())}")

            # Check for organic results
            if 'organic_results' in results:
                print(f"  Organic results: {len(results['organic_results'])} found")
            return True
        else:
            print("⚠️  Unexpected response format")
            return False

    except ProxyClientError as e:
        print(f"⚠️  Proxy error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_firecrawl_wrapper():
    """Test Firecrawl wrapper client"""
    print("\n" + "=" * 70)
    print("TEST 3: Firecrawl Wrapper Client")
    print("=" * 70)

    try:
        # Test initialization
        client = FirecrawlClient()
        print("✓ Client initialized successfully")

        # Test scrape
        print("  Testing URL scraping...")
        result = client.scrape_url("https://example.com")

        if result and result.get('success'):
            print(f"✓ Scraping successful")

            # Check for data
            if 'data' in result:
                data = result['data']
                if 'markdown' in data:
                    preview = data['markdown'][:100]
                    print(f"  Markdown preview: {preview}...")
            return True
        else:
            print(f"⚠️  Scraping response: {result}")
            return False

    except ProxyClientError as e:
        print(f"⚠️  Proxy error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_firecrawl_search():
    """Test Firecrawl search functionality"""
    print("\n" + "=" * 70)
    print("TEST 4: Firecrawl Search")
    print("=" * 70)

    try:
        client = FirecrawlClient()
        print("✓ Client initialized successfully")

        # Test search
        print("  Testing web search...")
        result = client.search(query="Python programming", limit=5)

        if result and result.get('success'):
            print(f"✓ Search successful")

            # Check for search results
            if 'data' in result and 'web' in result['data']:
                results = result['data']['web']
                print(f"  Found {len(results)} results")
                if results:
                    print(f"  First result: {results[0].get('title', 'N/A')}")
            return True
        else:
            print(f"⚠️  Search response: {result}")
            return False

    except ProxyClientError as e:
        print(f"⚠️  Proxy error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_tavily_wrapper():
    """Test Tavily wrapper client"""
    print("\n" + "=" * 70)
    print("TEST 5: Tavily Wrapper Client")
    print("=" * 70)

    try:
        # Test initialization
        client = TavilyClient()
        print("✓ Client initialized successfully")

        # Test search
        print("  Testing AI-powered search...")
        results = client.search(
            query="Latest developments in AI",
            max_results=3,
            search_depth="basic"
        )

        if results and isinstance(results, dict):
            print(f"✓ Search successful")
            print(f"  Results keys: {', '.join(results.keys())}")

            # Check for answer
            if 'answer' in results:
                answer_preview = results['answer'][:100]
                print(f"  Answer preview: {answer_preview}...")

            # Check for sources
            if 'results' in results:
                print(f"  Sources: {len(results['results'])} found")

            return True
        else:
            print("⚠️  Unexpected response format")
            return False

    except ProxyClientError as e:
        print(f"⚠️  Proxy error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_context_manager():
    """Test context manager support"""
    print("\n" + "=" * 70)
    print("TEST 6: Context Manager Support")
    print("=" * 70)

    try:
        # Test with context manager
        with TavilyClient() as client:
            print("✓ Context manager entered successfully")
            results = client.search("test query", max_results=1)
            print("✓ Request within context manager succeeded")

        print("✓ Context manager exited successfully")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_factory_functions():
    """Test factory and singleton functions"""
    print("\n" + "=" * 70)
    print("TEST 7: Factory and Singleton Functions")
    print("=" * 70)

    try:
        # Test factory function
        client1 = create_elevenlabs_client()
        print("✓ Factory function works")

        # Test singleton function
        client2 = get_tavily_client()
        client3 = get_tavily_client()
        is_same = client2 is client3
        print(f"✓ Singleton function works (same instance: {is_same})")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 70)
    print("TEST 8: Error Handling")
    print("=" * 70)

    try:
        # Test missing API key
        original_key = os.environ.pop('AIAPI_KEY', None)

        try:
            client = TavilyClient()
            print("❌ Should have raised error for missing API key")
            return False
        except ProxyClientError as e:
            print(f"✓ Correctly raised error for missing API key")

        # Restore API key
        if original_key:
            os.environ['AIAPI_KEY'] = original_key

        return True

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        # Restore API key
        if original_key:
            os.environ['AIAPI_KEY'] = original_key
        return False


def main():
    """Run all tests"""

    # Run all tests
    test_results['elevenlabs'] = test_elevenlabs_wrapper()
    test_results['serpapi'] = test_serpapi_wrapper()
    test_results['firecrawl_scrape'] = test_firecrawl_wrapper()
    test_results['firecrawl_search'] = test_firecrawl_search()
    test_results['tavily'] = test_tavily_wrapper()
    test_results['context_manager'] = test_context_manager()
    test_results['factory_functions'] = test_factory_functions()
    test_results['error_handling'] = test_error_handling()

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

    # Usage examples
    print("\n" + "=" * 70)
    print("USAGE EXAMPLES")
    print("=" * 70)
    print("""
# Basic usage
from infiniproxy_clients import TavilyClient, FirecrawlClient

# Initialize client
tavily = TavilyClient()
results = tavily.search("AI news")

# With context manager
with FirecrawlClient() as firecrawl:
    data = firecrawl.scrape_url("https://example.com")

# Using factory functions
from infiniproxy_clients import create_tavily_client
client = create_tavily_client()

# Using singleton (for efficiency)
from infiniproxy_clients import get_tavily_client
client = get_tavily_client()  # Reuses same instance
""")
    print("=" * 70)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
