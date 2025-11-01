# InfiniProxy Client Configuration Guide

This guide explains how to configure API clients to use InfiniProxy instead of connecting directly to original API endpoints.

## Overview

InfiniProxy acts as a unified gateway for multiple API services:
- **OpenAI** (Chat, Completions, Embeddings, etc.)
- **Anthropic/Claude** (Messages API)
- **Firecrawl** (Scrape, Crawl, Search)
- **ElevenLabs** (TTS, STT, WebSocket streaming)
- **Tavily** (Web Search)
- **SerpAPI** (Google Search)

By configuring your API clients to use the proxy, you get:
- ✅ Unified authentication (single API key)
- ✅ Usage tracking and analytics
- ✅ Centralized logging and monitoring
- ✅ Rate limiting and cost control
- ✅ Consistent error handling

## Quick Start

### Option 1: Bash Script (Recommended for CLI)

```bash
# Configure environment for proxy
source set_proxy_env.sh

# Test OpenAI endpoint
curl $OPENAI_API_BASE/models -H "Authorization: Bearer $OPENAI_API_KEY"

# When done, restore original settings
source unset_proxy_env.sh
```

### Option 2: Python Script (Recommended for Python projects)

```python
# In your Python code
from set_proxy_env import configure_proxy

# Configure environment
configure_proxy()

# Now use any API client normally
import openai
response = openai.ChatCompletion.create(...)
```

### Option 3: Environment File (Recommended for Docker/docker-compose)

```bash
# Copy template and customize
cp proxy.env.template .env

# Edit .env with your proxy URL and API key
nano .env

# Use with docker-compose
docker-compose --env-file .env up

# Or export in shell
export $(cat .env | xargs)
```

## Detailed Usage

### Bash Script Configuration

**Basic Usage:**
```bash
# Use default localhost:8000
source set_proxy_env.sh

# Use custom host
source set_proxy_env.sh api.example.com
source set_proxy_env.sh proxy.company.com:9000
```

**Custom API Key:**
```bash
# Set custom API key before running script
export INFINIPROXY_API_KEY="your-proxy-api-key-here"
source set_proxy_env.sh
```

**Cleanup:**
```bash
# Remove all proxy environment variables
source unset_proxy_env.sh
```

### Python Script Configuration

**Command Line Usage:**
```bash
# Print summary
python set_proxy_env.py

# Use custom host
python set_proxy_env.py api.example.com

# Generate bash export statements
python set_proxy_env.py --export > /tmp/proxy_env.sh
source /tmp/proxy_env.sh

# Generate JSON configuration
python set_proxy_env.py --json
```

**Programmatic Usage:**
```python
from set_proxy_env import configure_proxy

# Configure with defaults
config = configure_proxy()

# Configure with custom host
config = configure_proxy("api.example.com")

# Access configuration
print(f"Proxy URL: {config['proxy_url']}")
print(f"API Key: {config['proxy_api_key']}")
```

**Integration Examples:**

```python
# Example 1: OpenAI
from set_proxy_env import configure_proxy
import openai

configure_proxy()
# OpenAI client now automatically uses proxy

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

```python
# Example 2: Anthropic Claude
from set_proxy_env import configure_proxy
import anthropic

configure_proxy()
# Anthropic client now automatically uses proxy

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

```python
# Example 3: LangChain
from set_proxy_env import configure_proxy
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

configure_proxy()
# LangChain now uses proxy for all API calls

chat = ChatOpenAI(model="gpt-4")
response = chat([HumanMessage(content="Hello!")])
```

### Environment File Configuration

**Template Customization:**
```bash
# 1. Copy template
cp proxy.env.template proxy.env

# 2. Edit values
nano proxy.env

# Change these lines:
# INFINIPROXY_URL=https://your-proxy-domain.com
# INFINIPROXY_API_KEY=your-actual-api-key
```

**Usage Scenarios:**

**Scenario 1: Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: your-app
    env_file:
      - proxy.env
```

**Scenario 2: direnv (auto-load on cd)**
```bash
# Copy to .envrc
cp proxy.env.template .envrc

# Allow direnv
direnv allow

# Environment auto-loads when you cd into directory
```

**Scenario 3: systemd service**
```ini
# /etc/systemd/system/myapp.service
[Service]
EnvironmentFile=/path/to/proxy.env
ExecStart=/usr/bin/myapp
```

**Scenario 4: Manual export**
```bash
# Load all variables at once
export $(cat proxy.env | xargs)

# Verify
echo $OPENAI_API_BASE
```

## Configuration Reference

### Environment Variables by Service

#### OpenAI
```bash
OPENAI_API_BASE=http://localhost:8000/v1
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=your-proxy-api-key
```

**Supported Endpoints:**
- `/v1/chat/completions` - Chat completions
- `/v1/completions` - Text completions
- `/v1/embeddings` - Embeddings
- `/v1/models` - Model listing
- `/v1/audio/transcriptions` - Whisper transcription
- `/v1/audio/speech` - TTS

#### Anthropic/Claude
```bash
ANTHROPIC_BASE_URL=http://localhost:8000/v1
ANTHROPIC_API_URL=http://localhost:8000/v1
ANTHROPIC_API_KEY=your-proxy-api-key
```

**Supported Endpoints:**
- `/v1/messages` - Messages API
- `/v1/messages` (streaming) - Streaming responses

#### Firecrawl
```bash
FIRECRAWL_BASE_URL=http://localhost:8000/v1/firecrawl
FIRECRAWL_API_KEY=your-proxy-api-key
```

**Supported Endpoints:**
- `/v1/firecrawl/scrape` - Scrape single URL
- `/v1/firecrawl/crawl` - Start crawl job
- `/v1/firecrawl/crawl/status/{id}` - Check crawl status
- `/v1/firecrawl/search` - Web search (v2 API)

#### ElevenLabs
```bash
ELEVENLABS_API_BASE=http://localhost:8000/v1/elevenlabs
ELEVENLABS_BASE_URL=http://localhost:8000/v1/elevenlabs
ELEVEN_API_KEY=your-proxy-api-key
ELEVENLABS_API_KEY=your-proxy-api-key
```

**Supported Endpoints:**
- `/v1/elevenlabs/text-to-speech` - TTS
- `/v1/elevenlabs/text-to-speech/stream` - TTS streaming
- `/v1/elevenlabs/speech-to-text` - STT (requires premium)
- WebSocket: `ws://localhost:8000/v1/elevenlabs/text-to-speech/websocket`
- WebSocket: `ws://localhost:8000/v1/elevenlabs/speech-to-text/websocket`

#### Tavily
```bash
TAVILY_API_BASE=http://localhost:8000/v1/tavily
TAVILY_BASE_URL=http://localhost:8000/v1/tavily
TAVILY_API_KEY=your-proxy-api-key
```

**Supported Endpoints:**
- `/v1/tavily/search` - Web search
- `/v1/tavily/extract` - URL content extraction

#### SerpAPI
```bash
SERPAPI_BASE_URL=http://localhost:8000/v1/serpapi
SERPAPI_API_KEY=your-proxy-api-key
```

**Supported Endpoints:**
- `/v1/serpapi/search` - Google search
- `/v1/serpapi/search/google` - Google search
- `/v1/serpapi/search/images` - Google Images
- `/v1/serpapi/search/news` - Google News
- `/v1/serpapi/search/shopping` - Google Shopping

## Testing Configuration

### Verify Proxy Connection

```bash
# Source configuration
source set_proxy_env.sh

# Test health endpoint
curl http://localhost:8000/health

# Test OpenAI models endpoint
curl $OPENAI_API_BASE/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test Claude messages endpoint
curl $ANTHROPIC_BASE_URL/messages \
  -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test Firecrawl scrape
curl -X POST $FIRECRAWL_BASE_URL/scrape \
  -H "Authorization: Bearer $FIRECRAWL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "formats": ["markdown"]}'
```

### Python Test Script

```python
from set_proxy_env import configure_proxy
import os

# Configure environment
config = configure_proxy()

print("✅ Configuration loaded:")
print(f"  Proxy URL: {config['proxy_url']}")
print(f"  API Key: {config['proxy_api_key'][:20]}...")
print()

# Verify environment variables
services = ["OPENAI", "ANTHROPIC", "FIRECRAWL", "ELEVENLABS", "TAVILY", "SERPAPI"]
for service in services:
    base_url = os.getenv(f"{service}_BASE_URL") or os.getenv(f"{service}_API_BASE")
    api_key = os.getenv(f"{service}_API_KEY")
    if base_url and api_key:
        print(f"✅ {service}: {base_url}")
```

## Troubleshooting

### Issue: Environment variables not set

**Solution:**
```bash
# Make sure to SOURCE the script, not execute it
source set_proxy_env.sh  # ✅ Correct
./set_proxy_env.sh       # ❌ Wrong - creates subshell
```

### Issue: Permission denied

**Solution:**
```bash
# Make scripts executable
chmod +x set_proxy_env.sh
chmod +x unset_proxy_env.sh
chmod +x set_proxy_env.py
```

### Issue: Variables not persisting

**Symptom:** Variables disappear after closing terminal

**Solution:** Add to shell profile for persistence
```bash
# Add to ~/.bashrc or ~/.zshrc
# Load proxy configuration on shell startup
source /path/to/infiniproxy/set_proxy_env.sh
```

### Issue: API client not using proxy

**Symptom:** Requests still go to original API

**Debug Steps:**
```bash
# 1. Verify environment variables are set
env | grep -E "(OPENAI|ANTHROPIC|FIRECRAWL)"

# 2. Check if client library supports base URL override
# Some libraries may need explicit configuration

# 3. For Python, verify os.environ has the variables
python -c "import os; print(os.getenv('OPENAI_BASE_URL'))"
```

**Common Fixes:**
```python
# Some libraries need explicit configuration
import openai

# Option 1: Configure via environment (preferred)
from set_proxy_env import configure_proxy
configure_proxy()

# Option 2: Configure explicitly
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "your-proxy-api-key"
```

### Issue: WebSocket connections failing

**Solution:**
```bash
# WebSocket URLs use ws:// or wss:// protocol
WS_URL="ws://localhost:8000/v1/elevenlabs/text-to-speech/websocket"

# Not http:// or https://
# ❌ http://localhost:8000/v1/elevenlabs/text-to-speech/websocket
# ✅ ws://localhost:8000/v1/elevenlabs/text-to-speech/websocket
```

## Production Deployment

### Using Production Proxy

```bash
# Configure for production proxy
export INFINIPROXY_API_KEY="your-production-api-key"
source set_proxy_env.sh proxy.production.com
```

### Docker Production Setup

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    image: your-app:latest
    environment:
      - INFINIPROXY_URL=https://proxy.production.com
      - INFINIPROXY_API_KEY=${PROXY_API_KEY}
    env_file:
      - proxy.env
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: proxy-config
data:
  INFINIPROXY_URL: "https://proxy.production.com"
  OPENAI_BASE_URL: "https://proxy.production.com/v1"
  ANTHROPIC_BASE_URL: "https://proxy.production.com/v1"
  # ... other variables
---
apiVersion: v1
kind: Secret
metadata:
  name: proxy-secret
type: Opaque
stringData:
  INFINIPROXY_API_KEY: "your-production-api-key"
```

## Best Practices

1. **Security:**
   - Never commit API keys to version control
   - Use different API keys for dev/staging/production
   - Rotate API keys regularly

2. **Environment Management:**
   - Use `.env` files for local development
   - Use secrets managers (Vault, AWS Secrets Manager) for production
   - Keep environment files out of git (add to `.gitignore`)

3. **Testing:**
   - Test proxy configuration in staging before production
   - Monitor usage metrics to ensure proxy is being used
   - Keep fallback configuration for original APIs

4. **Documentation:**
   - Document which services use the proxy
   - Keep track of proxy endpoints and versions
   - Update configuration when proxy URLs change

## Files Reference

| File | Purpose | Usage |
|------|---------|-------|
| `set_proxy_env.sh` | Bash environment setup | `source set_proxy_env.sh` |
| `unset_proxy_env.sh` | Bash environment cleanup | `source unset_proxy_env.sh` |
| `set_proxy_env.py` | Python environment setup | `python set_proxy_env.py` |
| `proxy.env.template` | Environment file template | Copy and customize |

## Support

For issues or questions:
1. Check the proxy server health: `curl http://localhost:8000/health`
2. Review container logs: `docker logs infiniproxy-test`
3. Verify API key is valid: Check admin dashboard or database
4. Test individual endpoints with curl before using in code

## Additional Resources

- **Proxy Server Documentation**: See `README.md` for server setup
- **API Integration Guides**: See `FIRECRAWL_INTEGRATION.md`, etc.
- **WebSocket Testing**: See `ELEVENLABS_WEBSOCKET_TESTING.md`
- **Docker Setup**: See `Dockerfile` and docker-compose configuration
