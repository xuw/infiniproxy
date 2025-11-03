# Client Library Compatibility Guide

**Last Updated**: 2025-11-03
**Test Status**: ✅ Direct API calls fully supported (4/4 endpoints working)

## Quick Summary

✅ **RECOMMENDED**: Use direct API calls with `requests` library
⚠️ **LIMITED**: Official third-party client libraries (hardcoded base URLs)
✅ **SUPPORTED**: OpenAI and Anthropic official SDKs via environment variables

## Test Results

### Direct API Calls (Recommended Method)
| Endpoint | Status | Method |
|----------|--------|--------|
| Firecrawl Scrape | ✅ Working | POST /v1/firecrawl/scrape |
| Firecrawl Search | ✅ Working | POST /v1/firecrawl/search |
| Tavily Search | ✅ Working | POST /v1/tavily/search |
| SerpAPI Search | ✅ Working | GET /v1/serpapi/search |
| ElevenLabs TTS | ✅ Working | POST /v1/elevenlabs/text-to-speech |

### Official Client Libraries
| Library | Base URL Support | Status | Recommendation |
|---------|------------------|--------|----------------|
| `elevenlabs` | Partial | ⚠️ Limited | Use direct API calls |
| `google-search-results` | No | ❌ Not Supported | Use direct API calls |
| `firecrawl-py` | Yes (api_url) | ⚠️ API Changes | Use direct API calls |
| `tavily-python` | No | ❌ Not Supported | Use direct API calls |
| `openai` | Yes | ✅ Supported | Use OPENAI_BASE_URL env var |
| `anthropic` | Yes | ✅ Supported | Use ANTHROPIC_BASE_URL env var |

### Environment Variable Configuration
| Feature | Status | Notes |
|---------|--------|-------|
| .env file support | ✅ Working | python-dotenv compatible |
| AIAPI_URL/KEY | ✅ Working | New standard variables |
| INFINIPROXY_URL/KEY | ✅ Working | Backward compatible |
| OPENAI_BASE_URL | ✅ Working | OpenAI SDK support |
| ANTHROPIC_BASE_URL | ✅ Working | Anthropic SDK support |

## Usage Patterns

### 1. Direct API Calls (Recommended) ✅

**Why**: Full control, works with all endpoints, no dependency issues

```python
import os
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Get proxy configuration
proxy_url = os.environ["AIAPI_URL"]
api_key = os.environ["AIAPI_KEY"]

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Example: Firecrawl Scrape
response = requests.post(
    f"{proxy_url}/v1/firecrawl/scrape",
    headers=headers,
    json={"url": "https://example.com"}
)
print(response.json())

# Example: Tavily Search
response = requests.post(
    f"{proxy_url}/v1/tavily/search",
    headers=headers,
    json={"query": "Python programming", "max_results": 5}
)
print(response.json())

# Example: ElevenLabs TTS
response = requests.post(
    f"{proxy_url}/v1/elevenlabs/text-to-speech",
    headers=headers,
    json={"text": "Hello world!", "model_id": "eleven_monolingual_v1"}
)
# Save audio
with open("output.mp3", "wb") as f:
    f.write(response.content)
```

### 2. OpenAI SDK ✅

**Why**: Official SDK support via environment variables

```python
import openai
from dotenv import load_dotenv

# Load .env with OPENAI_BASE_URL and OPENAI_API_KEY
load_dotenv()

# SDK automatically uses OPENAI_BASE_URL from environment
client = openai.OpenAI()

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

**Environment variables required**:
```bash
OPENAI_BASE_URL=https://aiapi.iiis.co:9443/v1
OPENAI_API_KEY=your-proxy-api-key
```

### 3. Anthropic SDK ✅

**Why**: Official SDK support via environment variables

```python
import anthropic
from dotenv import load_dotenv

# Load .env with ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY
load_dotenv()

# SDK automatically uses ANTHROPIC_BASE_URL from environment
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-3-haiku-20240307",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.content[0].text)
```

**Environment variables required**:
```bash
ANTHROPIC_BASE_URL=https://aiapi.iiis.co:9443/v1
ANTHROPIC_API_KEY=your-proxy-api-key
```

### 4. Third-Party Client Libraries ⚠️

**Why Limited**: Most client libraries are hardcoded to official service URLs

**ElevenLabs Client**:
```python
from elevenlabs.client import ElevenLabs

# Client initializes but expects ElevenLabs-specific response format
client = ElevenLabs(
    api_key=os.environ["AIAPI_KEY"],
    base_url=os.environ["AIAPI_URL"]  # May work partially
)

# ⚠️ Limited compatibility - use direct API calls instead
```

**SerpAPI Client**:
```python
from serpapi import GoogleSearch

# ❌ No base_url parameter support
# Client is hardcoded to serpapi.com
# Use direct API calls to proxy instead
```

**Firecrawl Client**:
```python
from firecrawl import FirecrawlApp

# May support api_url parameter, but API compatibility issues
client = FirecrawlApp(
    api_key=os.environ["AIAPI_KEY"],
    api_url=os.environ["AIAPI_URL"]  # May not work
)

# ⚠️ API version differences - use direct API calls instead
```

**Tavily Client**:
```python
from tavily import TavilyClient

# ❌ No base_url parameter support
# Client is hardcoded to api.tavily.com
# Use direct API calls to proxy instead
```

## Environment Setup

### .env File Example

Copy `.env.example` to `.env` and configure:

```bash
# Proxy Configuration
AIAPI_URL=https://aiapi.iiis.co:9443
AIAPI_KEY=your-proxy-api-key-here

# OpenAI SDK
OPENAI_BASE_URL=https://aiapi.iiis.co:9443/v1
OPENAI_API_KEY=your-proxy-api-key-here

# Anthropic SDK
ANTHROPIC_BASE_URL=https://aiapi.iiis.co:9443/v1
ANTHROPIC_API_KEY=your-proxy-api-key-here
```

### Loading Environment Variables

**Python (recommended)**:
```python
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file
```

**Shell**:
```bash
# Load into current shell
source .env

# Or export all variables
export $(cat .env | xargs)
```

**Python without dotenv**:
```python
import os

# Set manually
os.environ["AIAPI_URL"] = "https://aiapi.iiis.co:9443"
os.environ["AIAPI_KEY"] = "your-api-key"
```

## API Endpoint Reference

### Chat Completions
```python
# OpenAI-compatible
POST /v1/chat/completions
{
  "model": "gpt-3.5-turbo",
  "messages": [{"role": "user", "content": "Hello"}]
}

# Claude/Anthropic-compatible
POST /v1/messages
{
  "model": "claude-3-haiku-20240307",
  "max_tokens": 1024,
  "messages": [{"role": "user", "content": "Hello"}]
}
```

### Firecrawl
```python
# Scrape
POST /v1/firecrawl/scrape
{"url": "https://example.com"}

# Search
POST /v1/firecrawl/search
{"query": "search term"}
```

### Tavily
```python
POST /v1/tavily/search
{
  "query": "search term",
  "max_results": 5
}
```

### SerpAPI
```python
GET /v1/serpapi/search?q=search+term&num=5
```

### ElevenLabs
```python
# TTS
POST /v1/elevenlabs/text-to-speech
{
  "text": "Hello world",
  "model_id": "eleven_monolingual_v1"
}

# WebSocket TTS
WS /v1/elevenlabs/text-to-speech/websocket
```

## Best Practices

### 1. Use Environment Variables
✅ Store API keys in .env files
✅ Never commit .env to version control
✅ Use .env.example as a template
❌ Don't hardcode API keys in code

### 2. Error Handling
```python
import requests

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()  # Raises exception for 4xx/5xx
    result = response.json()
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e.response.status_code}")
    print(f"Response: {e.response.text}")
except Exception as e:
    print(f"Error: {e}")
```

### 3. Use Requests Library
✅ Full control over requests
✅ Works with all proxy endpoints
✅ Easy to debug
✅ No dependency version conflicts

### 4. Test Before Production
```python
# Test health endpoint first
response = requests.get(f"{proxy_url}/health")
assert response.status_code == 200

# Then test your specific endpoint
response = requests.post(...)
```

## Troubleshooting

### Issue: "Connection refused"
**Solution**: Check that AIAPI_URL includes the correct port (9443)
```bash
# Correct
AIAPI_URL=https://aiapi.iiis.co:9443

# Wrong
AIAPI_URL=https://aiapi.iiis.co
```

### Issue: "401 Unauthorized"
**Solution**: Verify API key is set correctly
```python
# Check environment variable
print(os.environ.get("AIAPI_KEY"))

# Verify header format
headers = {"Authorization": f"Bearer {api_key}"}
```

### Issue: "SSL verification failed"
**Solution**: For development, you can disable SSL verification (not recommended for production)
```python
response = requests.post(url, headers=headers, json=data, verify=False)
```

### Issue: Client library not working
**Solution**: Use direct API calls instead of official client libraries
```python
# Instead of:
# client = SomeClient(api_key=key, base_url=url)

# Use:
response = requests.post(
    f"{url}/v1/endpoint",
    headers={"Authorization": f"Bearer {key}"},
    json=payload
)
```

## Testing

Run compatibility tests:
```bash
# Full endpoint tests
python test_all_endpoints.py

# Client compatibility tests
python test_official_clients.py
```

Expected results:
- **test_all_endpoints.py**: 8/8 tests passing (100%)
- **test_official_clients.py**: Direct API calls working (4/4)

## Support

For issues or questions:
- Check proxy health: `curl https://aiapi.iiis.co:9443/health`
- Review logs: `kubectl logs deployment/infiniproxy -n weixu`
- Test configuration: `python test_proxy_client_config.py`
- See examples: `test_all_endpoints.py`, `test_official_clients.py`

---

**Key Takeaway**: Direct API calls with the `requests` library provide the most reliable and flexible way to use the InfiniProxy service. Official SDKs (OpenAI, Anthropic) also work well via environment variables.
