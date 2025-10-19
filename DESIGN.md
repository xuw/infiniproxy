# OpenAI to Claude API Proxy - Design Document

## Overview
A local proxy server that translates between OpenAI-compatible API format and Claude (Anthropic) API format, allowing Claude Code to use OpenAI-compatible backends.

## Architecture

```
Claude Code → HTTP Request (Claude Format) → Proxy Server → HTTP Request (OpenAI Format) → Infini AI
                                                ↓
Claude Code ← HTTP Response (Claude Format) ← Proxy Server ← HTTP Response (OpenAI Format) ← Infini AI
```

## API Format Differences

### Claude API Request Format
```json
{
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 1024,
  "messages": [
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "system": "You are a helpful assistant",
  "temperature": 0.7,
  "stream": false
}
```

### OpenAI API Request Format
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant"
    },
    {
      "role": "user",
      "content": "Hello"
    }
  ],
  "max_tokens": 1024,
  "temperature": 0.7,
  "stream": false
}
```

### Claude API Response Format
```json
{
  "id": "msg_123",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello! How can I help you?"
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20
  }
}
```

### OpenAI API Response Format
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

## Translation Logic

### Request Translation (Claude → OpenAI)

1. **Model Mapping**
   - Extract `model` from Claude request
   - Map to configured OpenAI model (e.g., "glm-4.6")

2. **System Message Handling**
   - Extract `system` field from Claude request
   - Insert as first message with `role: "system"` in OpenAI request

3. **Messages Conversion**
   - Convert Claude's content blocks to simple string content
   - Handle text-only content (image support can be added later)

4. **Parameters**
   - `max_tokens`: Direct mapping
   - `temperature`: Direct mapping
   - `stream`: Direct mapping

### Response Translation (OpenAI → Claude)

1. **Message Structure**
   - Extract `choices[0].message.content` from OpenAI
   - Wrap in Claude's content block format: `[{"type": "text", "text": "..."}]`

2. **Metadata**
   - `id`: Use OpenAI's `id` or generate unique ID
   - `type`: Always "message"
   - `role`: Always "assistant"
   - `model`: Return original requested Claude model
   - `stop_reason`: Map OpenAI's `finish_reason` to Claude's stop reasons
     - "stop" → "end_turn"
     - "length" → "max_tokens"
     - "content_filter" → "content_filtered"

3. **Usage Statistics**
   - `input_tokens`: Map from `usage.prompt_tokens`
   - `output_tokens`: Map from `usage.completion_tokens`

## Implementation Components

### 1. Proxy Server (`proxy_server.py`)
- FastAPI/Flask HTTP server
- Endpoint: `POST /v1/messages` (Claude format)
- Configuration: Environment variables or config file
- Error handling and logging

### 2. Translation Module (`translator.py`)
- `translate_request_to_openai(claude_request) -> openai_request`
- `translate_response_to_claude(openai_response) -> claude_response`
- Handle edge cases and validation

### 3. OpenAI Client (`openai_client.py`)
- HTTP client for OpenAI-compatible endpoint
- Handle authentication (Bearer token)
- Support streaming and non-streaming

### 4. Configuration (`config.py`)
- OpenAI endpoint URL
- API key
- Model name
- Port for proxy server

## Testing Strategy

### Unit Tests
1. Request translation correctness
2. Response translation correctness
3. Error handling
4. Edge cases (empty messages, special characters)

### Integration Tests
1. End-to-end proxy flow with mock OpenAI backend
2. Streaming response handling
3. Error response handling

### Manual Tests
1. Test with actual Claude Code
2. Verify compatibility with different request types

## Configuration

### Environment Variables
```bash
OPENAI_BASE_URL=https://cloud.infini-ai.com/maas/v1/chat/completions
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=glm-4.6
PROXY_PORT=8000
PROXY_HOST=localhost
```

## Future Enhancements
- Streaming support (SSE)
- Image content support
- Multiple model mapping
- Request/response logging
- Rate limiting
- Caching
- Health check endpoint
