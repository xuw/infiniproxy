# OpenAI to Claude API Proxy

A local proxy server that translates between OpenAI-compatible API format and Claude (Anthropic) API format, allowing Claude Code and other Claude-based tools to use OpenAI-compatible backends.

## Features

- ✅ Translates Claude API requests to OpenAI format
- ✅ Translates OpenAI responses back to Claude format
- ✅ Handles system messages properly
- ✅ Supports multi-turn conversations
- ✅ Handles Claude's content blocks
- ✅ **Full tool/function calling support**
- ✅ Special support for reasoning models (like glm-4.6)
- ✅ Comprehensive test suite
- ✅ Easy configuration via environment variables

## Architecture

```
Claude Code → HTTP (Claude Format) → Proxy Server → HTTP (OpenAI Format) → OpenAI-Compatible Backend
                                           ↓
Claude Code ← HTTP (Claude Format) ← Proxy Server ← HTTP (OpenAI Format) ← OpenAI-Compatible Backend
```

## Installation

1. Clone or download this repository
2. Create a virtual environment and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Configure the environment variables:

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env with your settings
nano .env
```

## Configuration

Edit the `.env` file with your settings:

```bash
# OpenAI-compatible backend configuration
OPENAI_BASE_URL=https://cloud.infini-ai.com/maas/v1/chat/completions
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=glm-4.6

# Proxy server configuration
PROXY_HOST=localhost
PROXY_PORT=8000

# Optional settings
TIMEOUT=300
DEBUG=false
```

## Usage

### Starting the Proxy Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the proxy server
python proxy_server.py
```

The server will start on `http://localhost:8000` (or your configured port).

### Using with Claude Code

Configure Claude Code to use the proxy as its API endpoint:

1. Set the API endpoint to: `http://localhost:8000`
2. The proxy accepts Claude API format at `/v1/messages`

### API Endpoints

#### `GET /`
Returns server information and available endpoints.

```bash
curl http://localhost:8000/
```

#### `GET /health`
Health check endpoint.

```bash
curl http://localhost:8000/health
```

#### `POST /v1/messages`
Main endpoint for creating messages (Claude API format).

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
source venv/bin/activate
pytest tests/ -v
```

### End-to-End Tests

Test the proxy with real API calls:

```bash
# Make sure the proxy server is running first
python proxy_server.py

# In another terminal:
source venv/bin/activate
python test_e2e.py
```

### Manual Testing

You can also use the test script to verify the OpenAI endpoint works:

```bash
source venv/bin/activate
python test_api.py
```

## API Translation Details

### Request Translation (Claude → OpenAI)

The proxy translates Claude API requests to OpenAI format:

- **System messages**: Extracted from `system` field and added as first message with `role: "system"`
- **Content blocks**: Claude's content blocks (e.g., `[{"type": "text", "text": "..."}]`) are converted to simple strings
- **Parameters**: `max_tokens`, `temperature`, `top_p`, `stop_sequences` are mapped appropriately

### Response Translation (OpenAI → Claude)

OpenAI responses are translated back to Claude format:

- **Message structure**: Wrapped in Claude's content block format
- **Stop reasons**: Mapped from OpenAI's `finish_reason` to Claude's `stop_reason`
  - `stop` → `end_turn`
  - `length` → `max_tokens`
  - `content_filter` → `content_filtered`
- **Usage tokens**: Mapped from `prompt_tokens`/`completion_tokens` to `input_tokens`/`output_tokens`
- **Reasoning content**: Special handling for models with `reasoning_content` (like glm-4.6)

## Project Structure

```
infiniproxy/
├── config.py              # Configuration management
├── translator.py          # Request/response translation logic
├── openai_client.py       # OpenAI API client
├── proxy_server.py        # Main proxy server (FastAPI)
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (not in git)
├── .gitignore            # Git ignore patterns
├── DESIGN.md             # Architecture and design document
├── README.md             # This file
├── test_api.py           # API verification script
├── test_e2e.py           # End-to-end tests
└── tests/                # Unit tests
    ├── __init__.py
    ├── test_translator.py
    └── test_proxy_server.py
```

## Limitations

- **Streaming**: Currently not fully implemented. Streaming requests fall back to non-streaming responses.
- **Images**: Image content blocks are not yet supported in translation.

## Troubleshooting

### Connection Refused
- Make sure the proxy server is running
- Check that the port (default 8000) is not in use by another application
- Verify firewall settings allow connections to localhost

### API Key Errors
- Verify your `OPENAI_API_KEY` in the `.env` file is correct
- Check that the OpenAI-compatible endpoint is accessible

### Translation Errors
- Enable debug logging by setting `DEBUG=true` in `.env`
- Check the server logs for detailed error messages
- Verify the request format matches Claude API specifications

### Tests Failing
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- For end-to-end tests, make sure the proxy server is running
- Check that the OpenAI backend endpoint is accessible

## Development

### Running in Development Mode

```bash
# Enable debug logging
export DEBUG=true

# Run with auto-reload
uvicorn proxy_server:app --reload --host localhost --port 8000
```

### Adding New Features

1. Update `translator.py` for translation logic changes
2. Update `openai_client.py` for client changes
3. Add tests in `tests/` directory
4. Update documentation

## License

This project is provided as-is for educational and development purposes.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review the DESIGN.md for architecture details
3. Open an issue on the repository
