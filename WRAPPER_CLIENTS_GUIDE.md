# InfiniProxy Wrapper Clients - Quick Start Guide

## Overview

The InfiniProxy wrapper client library provides drop-in replacements for popular API client libraries that work seamlessly with InfiniProxy. All clients maintain interface compatibility with their official counterparts while routing requests through your proxy.

## Installation

### Copy to Your Project
```bash
# Copy the wrapper library to your project
cp infiniproxy_clients.py /path/to/your/project/
```

### Or Install as Module
```bash
# Add to your Python path
export PYTHONPATH="/path/to/infiniproxy:$PYTHONPATH"
```

## Configuration

### Environment Variables

Set these environment variables (or use a `.env` file):

```bash
# Required
export AIAPI_KEY="your-proxy-api-key"

# Optional (defaults to https://aiapi.iiis.co:9443)
export AIAPI_URL="https://aiapi.iiis.co:9443"
```

### Using .env Files

```bash
# Create .env file
cat > .env << 'EOF'
AIAPI_URL=https://aiapi.iiis.co:9443
AIAPI_KEY=your-proxy-api-key
EOF

# Load with python-dotenv
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()

from infiniproxy_clients import TavilyClient
client = TavilyClient()  # Reads from environment
```

## Usage Examples

### ElevenLabs - Text-to-Speech

```python
from infiniproxy_clients import ElevenLabsClient

# Initialize client
client = ElevenLabsClient()

# Generate speech
audio = client.text_to_speech(
    text="Hello from InfiniProxy!",
    model_id="eleven_monolingual_v1"
)

# Save to file
with open("output.mp3", "wb") as f:
    f.write(audio)

# Alternative method name (compatible with official client)
audio = client.generate(text="Hello!", voice="default")
```

### SerpAPI - Google Search

```python
from infiniproxy_clients import SerpAPIClient

# Initialize client
client = SerpAPIClient()

# Perform search
results = client.search(
    query="Python programming",
    num=10
)

# Access results
for result in results['organic_results']:
    print(f"{result['title']}: {result['link']}")

# Alternative method (official client style)
results = client.get_results({'q': 'Python', 'num': 5})
```

### Firecrawl - Web Scraping

```python
from infiniproxy_clients import FirecrawlClient

# Initialize client
client = FirecrawlClient()

# Scrape single URL
result = client.scrape_url("https://example.com")
markdown = result['data']['markdown']
html = result['data']['html']

# Search the web
search_results = client.search(
    query="Python tutorials",
    limit=10
)

for item in search_results['data']['web']:
    print(f"{item['title']}: {item['url']}")

# Crawl entire website
crawl_results = client.crawl_url(
    url="https://example.com",
    max_depth=2,
    limit=50
)
```

### Tavily - AI-Powered Search

```python
from infiniproxy_clients import TavilyClient

# Initialize client
client = TavilyClient()

# Perform search
results = client.search(
    query="Latest AI developments",
    max_results=5,
    search_depth="basic"
)

# Get AI-generated answer
print(results['answer'])

# Access sources
for source in results['results']:
    print(f"{source['title']}: {source['url']}")

# Get context as string
context = client.get_search_context("What is machine learning?")

# Question-answering search
qa_results = client.qna_search("How does AI work?")
```

## Advanced Usage

### Context Manager (Recommended)

```python
from infiniproxy_clients import FirecrawlClient

# Automatically closes session on exit
with FirecrawlClient() as client:
    result = client.scrape_url("https://example.com")
    # Session closed automatically
```

### Custom Configuration

```python
from infiniproxy_clients import TavilyClient

# Override environment variables
client = TavilyClient(
    api_key="custom-api-key",
    base_url="https://custom-proxy.com:9443",
    timeout=60  # Custom timeout in seconds
)

results = client.search("query")
```

### Factory Functions

```python
from infiniproxy_clients import (
    create_elevenlabs_client,
    create_tavily_client
)

# Create clients with factory functions
elevenlabs = create_elevenlabs_client()
tavily = create_tavily_client(timeout=30)
```

### Singleton Pattern (For Efficiency)

```python
from infiniproxy_clients import (
    get_elevenlabs_client,
    get_tavily_client
)

# Get singleton instances (reuses same client)
client1 = get_tavily_client()
client2 = get_tavily_client()
assert client1 is client2  # Same instance

# Good for reducing connection overhead
tavily = get_tavily_client()
results1 = tavily.search("query 1")
results2 = tavily.search("query 2")  # Reuses session
```

## Error Handling

```python
from infiniproxy_clients import TavilyClient, ProxyClientError

try:
    client = TavilyClient()
    results = client.search("query")
except ProxyClientError as e:
    print(f"Proxy error: {e}")
    # Handle proxy-specific errors
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Migration from Official Clients

### Before (Official ElevenLabs Client)

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key="official-api-key")
audio = client.text_to_speech(
    text="Hello",
    voice=Voice(voice_id="default")
)
```

### After (InfiniProxy Wrapper)

```python
from infiniproxy_clients import ElevenLabsClient

# API key comes from AIAPI_KEY environment variable
client = ElevenLabsClient()
audio = client.text_to_speech(
    text="Hello",
    voice_id="default"
)
```

### Before (Official Tavily Client)

```python
from tavily import TavilyClient

client = TavilyClient(api_key="official-api-key")
results = client.search(query="AI news")
```

### After (InfiniProxy Wrapper)

```python
from infiniproxy_clients import TavilyClient

# API key comes from AIAPI_KEY environment variable
client = TavilyClient()
results = client.search(query="AI news")
```

## Performance Tips

1. **Reuse Client Instances**: Create clients once and reuse them
   ```python
   # Good
   client = TavilyClient()
   for query in queries:
       client.search(query)

   # Bad (creates new session each time)
   for query in queries:
       TavilyClient().search(query)
   ```

2. **Use Singleton for Global Access**:
   ```python
   from infiniproxy_clients import get_tavily_client

   # In module A
   tavily = get_tavily_client()

   # In module B (same instance)
   tavily = get_tavily_client()
   ```

3. **Context Managers for Short-Lived Usage**:
   ```python
   with FirecrawlClient() as client:
       result = client.scrape_url(url)
   # Session closed immediately
   ```

4. **Adjust Timeout for Slow Operations**:
   ```python
   client = FirecrawlClient(timeout=120)  # 2 minutes
   ```

## Comparison with Direct API Calls

### Wrapper Client (Recommended)
```python
from infiniproxy_clients import TavilyClient

client = TavilyClient()
results = client.search("query")
```

**Pros**:
- ✅ Clean, object-oriented interface
- ✅ Connection pooling and session reuse
- ✅ Type hints and documentation
- ✅ Error handling built-in
- ✅ Context manager support

### Direct API Calls
```python
import requests
import os

headers = {'Authorization': f"Bearer {os.getenv('AIAPI_KEY')}"}
response = requests.post(
    f"{os.getenv('AIAPI_URL')}/v1/tavily/search",
    headers=headers,
    json={'query': 'query'}
)
results = response.json()
```

**Pros**:
- ✅ No additional dependencies
- ✅ Full control over requests

**Cons**:
- ❌ More boilerplate code
- ❌ Manual session management
- ❌ Manual error handling

## Testing

Run the test suite:

```bash
python test_wrapper_clients.py
```

Expected output: `8/8 tests passing (100%)`

## Troubleshooting

### "API key required" Error

```python
ProxyClientError: API key required. Set AIAPI_KEY environment variable or pass api_key parameter.
```

**Solution**: Set the `AIAPI_KEY` environment variable:
```bash
export AIAPI_KEY="your-proxy-api-key"
```

### Connection Timeout

```python
ProxyClientError: Request timeout after 30s
```

**Solution**: Increase timeout:
```python
client = TavilyClient(timeout=120)
```

### HTTP 401 Unauthorized

```python
ProxyClientError: HTTP 401: Unauthorized
```

**Solution**: Check your API key is correct and has necessary permissions.

### HTTP 403 Forbidden

```python
ProxyClientError: HTTP 403: Forbidden
```

**Solution**: Verify your API key has access to the requested service.

## API Reference

### BaseProxyClient

Base class for all clients.

**Parameters**:
- `api_key` (str, optional): API key (defaults to AIAPI_KEY env var)
- `base_url` (str, optional): Base URL (defaults to AIAPI_URL env var)
- `timeout` (int, optional): Request timeout in seconds (default: 30)

**Methods**:
- `close()`: Close the session
- Context manager support: `with Client() as client:`

### ElevenLabsClient

**Methods**:
- `text_to_speech(text, model_id="eleven_monolingual_v1", voice_id=None, **kwargs) -> bytes`
- `generate(text, voice="default", model="eleven_monolingual_v1", **kwargs) -> bytes`

### SerpAPIClient

**Methods**:
- `search(query, num=10, engine="google", **kwargs) -> dict`
- `get_results(params) -> dict`

### FirecrawlClient

**Methods**:
- `scrape_url(url, formats=None, only_main_content=True, **kwargs) -> dict`
- `search(query, limit=10, **kwargs) -> dict`
- `crawl_url(url, max_depth=2, limit=None, **kwargs) -> dict`

### TavilyClient

**Methods**:
- `search(query, max_results=5, search_depth="basic", **kwargs) -> dict`
- `get_search_context(query, max_results=5, **kwargs) -> str`
- `qna_search(query, **kwargs) -> dict`

## Support

For issues or questions:
1. Check test results: `python test_wrapper_clients.py`
2. Verify environment variables: `echo $AIAPI_URL $AIAPI_KEY`
3. Test direct API calls: `python test_all_endpoints.py`
4. Review logs and error messages
