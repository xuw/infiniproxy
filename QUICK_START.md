# Quick Start Guide - InfiniProxy Client Configuration

## TL;DR

```bash
# 1. Set your configuration
export AIAPI_URL=http://localhost:8000
export AIAPI_KEY=your-proxy-api-key-here

# 2. Configure environment
source set_proxy_env.sh

# 3. Use any API client
curl $OPENAI_API_BASE/models -H "Authorization: Bearer $OPENAI_API_KEY"
```

## What This Does

Redirects all API clients to use your InfiniProxy server instead of calling APIs directly:

```
Your App → InfiniProxy → OpenAI/Claude/ElevenLabs/etc.
```

Benefits:
- ✅ Unified authentication (one API key for all services)
- ✅ Automatic usage tracking
- ✅ Centralized logging and monitoring
- ✅ Cost control and rate limiting

## Required Setup

### 1. Set Environment Variables

```bash
export AIAPI_URL=http://localhost:8000        # Your proxy server URL
export AIAPI_KEY=sk-your-proxy-api-key-here   # Your proxy API key
```

### 2. Choose Your Method

**Bash (for CLI/scripts):**
```bash
source set_proxy_env.sh
```

**Python (for code):**
```python
from set_proxy_env import configure_proxy
configure_proxy()
```

**.env file (for Docker/projects):**
```bash
cp proxy.env.template .env
# Edit .env with your values
export $(cat .env | xargs)
```

## Verify It Works

```bash
# Test health endpoint
curl $AIAPI_URL/health

# Test OpenAI
curl $OPENAI_API_BASE/models -H "Authorization: Bearer $OPENAI_API_KEY"

# Or run comprehensive tests
python test_proxy_client_config.py
```

## What Gets Configured

After running the scripts, these environment variables are automatically set:

| Service | Base URL Variable | API Key Variable |
|---------|------------------|------------------|
| OpenAI | `OPENAI_API_BASE` | `OPENAI_API_KEY` |
| Claude | `ANTHROPIC_BASE_URL` | `ANTHROPIC_API_KEY` |
| Firecrawl | `FIRECRAWL_BASE_URL` | `FIRECRAWL_API_KEY` |
| ElevenLabs | `ELEVENLABS_API_BASE` | `ELEVENLABS_API_KEY` |
| Tavily | `TAVILY_API_BASE` | `TAVILY_API_KEY` |
| SerpAPI | `SERPAPI_BASE_URL` | `SERPAPI_API_KEY` |

## Example Usage

### OpenAI Python Client

```python
import os
from set_proxy_env import configure_proxy
import openai

# Configure to use proxy
configure_proxy()

# Use OpenAI normally - automatically goes through proxy
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Anthropic Claude

```python
import os
from set_proxy_env import configure_proxy
import anthropic

# Configure to use proxy
configure_proxy()

# Use Claude normally - automatically goes through proxy
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### LangChain

```python
import os
from set_proxy_env import configure_proxy
from langchain.chat_models import ChatOpenAI

# Configure to use proxy
configure_proxy()

# All LangChain API calls now go through proxy
chat = ChatOpenAI(model="gpt-4")
response = chat([{"role": "user", "content": "Hello!"}])
```

### cURL

```bash
# After running: source set_proxy_env.sh

# OpenAI Chat
curl $OPENAI_API_BASE/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Claude Messages
curl $ANTHROPIC_BASE_URL/messages \
  -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Troubleshooting

### "AIAPI_KEY environment variable is not set"

**Fix:**
```bash
export AIAPI_KEY=your-actual-api-key
```

### Variables disappear after closing terminal

**Fix:** Add to `~/.bashrc` or `~/.zshrc`:
```bash
export AIAPI_URL=http://localhost:8000
export AIAPI_KEY=your-api-key
```

### Proxy server not running

**Fix:**
```bash
docker start infiniproxy-test
# Or run locally:
python proxy_server.py
```

## Production Deployment

```bash
# Set production values
export AIAPI_URL=https://proxy.production.com
export AIAPI_KEY=sk-production-key-here

# Configure
source set_proxy_env.sh

# Verify
curl $AIAPI_URL/health
```

## Next Steps

- **Full Documentation**: See `PROXY_CLIENT_SETUP.md`
- **Migration Guide**: See `MIGRATION_GUIDE.md` (if upgrading)
- **Server Setup**: See `README.md`
- **WebSocket Testing**: See `ELEVENLABS_WEBSOCKET_TESTING.md`

## Files Overview

| File | Purpose |
|------|---------|
| `set_proxy_env.sh` | Bash configuration script |
| `set_proxy_env.py` | Python configuration script |
| `proxy.env.template` | Environment file template |
| `test_proxy_client_config.py` | Test suite |
| `QUICK_START.md` | This file |
| `PROXY_CLIENT_SETUP.md` | Complete documentation |
| `MIGRATION_GUIDE.md` | Migration from old variables |
