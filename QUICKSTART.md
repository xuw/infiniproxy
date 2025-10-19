# Quick Start Guide

## What is this?

This proxy allows you to use an OpenAI-compatible API (like Infini AI's glm-4.6 model) with tools that expect Claude's API format, such as Claude Code.

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/xuw/infiniproxy
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration

The `.env` file needs to be configured with:
- **OpenAI Endpoint**: https://cloud.infini-ai.com/maas/v1/chat/completions
- **API Key**: Your API key (see .env.example)
- **Model**: glm-4.6
- **Proxy Port**: 8000

You can edit `.env` if you need to change any settings.

### 3. Start the Proxy

```bash
source venv/bin/activate
python proxy_server.py
```

You should see:
```
INFO - Proxy server initialized successfully
INFO - OpenAI backend: https://cloud.infini-ai.com/maas/v1/chat/completions
INFO - OpenAI model: glm-4.6
INFO - Proxy listening on: localhost:8000
```

### 4. Test It Works

In another terminal:

```bash
source venv/bin/activate
python test_e2e.py
```

You should see all tests pass! ✅

## Using with Claude Code

To use this proxy with Claude Code, configure Claude Code to use:

- **API Endpoint**: `http://localhost:8000`
- **Messages Endpoint**: `http://localhost:8000/v1/messages`

The proxy accepts Claude API format requests and translates them to OpenAI format automatically.

## Testing the API Directly

### Health Check
```bash
curl http://localhost:8000/health
```

### Send a Message
```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 200,
    "messages": [
      {
        "role": "user",
        "content": "Hello! Please introduce yourself."
      }
    ]
  }'
```

## What's Working

✅ **Request Translation**: Claude format → OpenAI format
✅ **Response Translation**: OpenAI format → Claude format
✅ **System Messages**: Properly handled and converted
✅ **Multi-turn Conversations**: Full conversation history support
✅ **Content Blocks**: Claude's content blocks → OpenAI simple strings
✅ **Reasoning Models**: Special handling for glm-4.6's reasoning_content
✅ **Usage Statistics**: Token counts properly mapped
✅ **Stop Reasons**: Finish reasons properly translated

## Troubleshooting

### Port Already in Use
```bash
# Change PROXY_PORT in .env to a different port
PROXY_PORT=8001
```

### Can't Connect to OpenAI Backend
- Check your internet connection
- Verify the API key is valid
- Test with: `python test_api.py`

### API Returns Errors
- Enable debug mode: Set `DEBUG=true` in `.env`
- Check the proxy server logs for details

## Next Steps

- Read [README.md](README.md) for full documentation
- See [DESIGN.md](DESIGN.md) for architecture details
- Check [tests/](tests/) for unit test examples

## Development

### Run Tests
```bash
source venv/bin/activate

# Unit tests
pytest tests/ -v

# End-to-end tests (requires proxy running)
python test_e2e.py
```

### Enable Debug Logging
```bash
# In .env file
DEBUG=true
```

### Auto-reload on Changes
```bash
source venv/bin/activate
uvicorn proxy_server:app --reload --host localhost --port 8000
```

## Architecture Overview

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│             │      │              │      │             │
│ Claude Code │─────▶│    Proxy     │─────▶│  Infini AI  │
│             │      │   (port 8000)│      │  (glm-4.6)  │
│             │◀─────│              │◀─────│             │
└─────────────┘      └──────────────┘      └─────────────┘
  Claude Format        Translation         OpenAI Format
```

The proxy handles all the translation automatically, so Claude Code thinks it's talking to Claude's API, while actually using the OpenAI-compatible backend.

## Project Structure

```
infiniproxy/
├── proxy_server.py      # Main server
├── translator.py        # Translation logic
├── openai_client.py     # OpenAI client
├── config.py            # Configuration
├── .env                 # Your settings
├── test_e2e.py          # End-to-end tests
├── tests/               # Unit tests
│   ├── test_translator.py
│   └── test_proxy_server.py
├── README.md            # Full documentation
├── DESIGN.md            # Architecture details
└── QUICKSTART.md        # This file
```

## Support

For issues or questions:
1. Check the logs (enable DEBUG=true)
2. Review the full [README.md](README.md)
3. Check [DESIGN.md](DESIGN.md) for technical details
