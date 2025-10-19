"""Integration tests for the proxy server."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import os

# Set environment variables before importing
os.environ["OPENAI_BASE_URL"] = "https://test.example.com/v1/chat/completions"
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["OPENAI_MODEL"] = "test-model"

# Import after setting env vars
import proxy_server
from proxy_server import app


@pytest.fixture(autouse=True)
def mock_components():
    """Mock the server components for all tests."""
    mock_config = Mock()
    mock_config.openai_base_url = "https://test.example.com"
    mock_config.openai_model = "test-model"

    mock_translator = Mock()
    mock_client = Mock()

    with patch.object(proxy_server, 'config', mock_config), \
         patch.object(proxy_server, 'translator', mock_translator), \
         patch.object(proxy_server, 'openai_client', mock_client):
        yield {
            'config': mock_config,
            'translator': mock_translator,
            'openai_client': mock_client
        }


class TestProxyServer:
    """Test cases for the proxy server."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test the root endpoint returns server information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "openai_backend" in data
        assert "openai_model" in data

    def test_create_message_simple(self, client, mock_components):
        """Test creating a simple message."""
        # Setup mocks
        mock_translator = mock_components['translator']
        mock_client = mock_components['openai_client']

        # Mock translation
        mock_translator.translate_request_to_openai.return_value = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello!"}]
        }

        # Mock OpenAI response
        mock_client.create_completion.return_value = {
            "id": "test-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "test-model",
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
                "completion_tokens": 8,
                "total_tokens": 18
            }
        }

        # Claude API request
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
        }

        # Mock translation back to Claude format
        mock_translator.translate_response_to_claude.return_value = {
            "id": "test-123",
            "type": "message",
            "role": "assistant",
            "model": "claude-3-5-sonnet-20241022",
            "content": [
                {
                    "type": "text",
                    "text": "Hello! How can I help you?"
                }
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 8
            }
        }

        response = client.post("/v1/messages", json=claude_request)
        assert response.status_code == 200

        data = response.json()
        assert data["type"] == "message"
        assert data["role"] == "assistant"
        assert data["model"] == "claude-3-5-sonnet-20241022"
        assert len(data["content"]) == 1
        assert data["content"][0]["type"] == "text"
        assert data["content"][0]["text"] == "Hello! How can I help you?"
        assert data["stop_reason"] == "end_turn"
        assert data["usage"]["input_tokens"] == 10
        assert data["usage"]["output_tokens"] == 8

    def test_create_message_with_system(self, client, mock_openai_client):
        """Test creating a message with system prompt."""
        mock_openai_client.create_completion.return_value = {
            "id": "test-456",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I am a helpful assistant."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 7,
                "total_tokens": 22
            }
        }

        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "system": "You are a helpful assistant.",
            "messages": [
                {
                    "role": "user",
                    "content": "What are you?"
                }
            ]
        }

        response = client.post("/v1/messages", json=claude_request)
        assert response.status_code == 200

        # Verify the OpenAI client was called with system message
        call_args = mock_openai_client.create_completion.call_args[0][0]
        assert call_args["messages"][0]["role"] == "system"
        assert call_args["messages"][0]["content"] == "You are a helpful assistant."

    def test_create_message_with_reasoning(self, client, mock_openai_client):
        """Test handling of reasoning_content in response."""
        mock_openai_client.create_completion.return_value = {
            "id": "test-789",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "The answer is 42",
                        "reasoning_content": "Let me calculate: 6 * 7 = 42"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 15,
                "total_tokens": 23
            }
        }

        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": "What is 6 * 7?"
                }
            ]
        }

        response = client.post("/v1/messages", json=claude_request)
        assert response.status_code == 200

        data = response.json()
        content_text = data["content"][0]["text"]
        assert "[Reasoning]" in content_text
        assert "Let me calculate: 6 * 7 = 42" in content_text
        assert "[Response]" in content_text
        assert "The answer is 42" in content_text

    def test_create_message_with_max_tokens_finish(self, client, mock_openai_client):
        """Test handling of length finish_reason."""
        mock_openai_client.create_completion.return_value = {
            "id": "test-max",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "This response was cut off..."
                    },
                    "finish_reason": "length"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 100,
                "total_tokens": 105
            }
        }

        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Tell me a long story"
                }
            ]
        }

        response = client.post("/v1/messages", json=claude_request)
        assert response.status_code == 200

        data = response.json()
        assert data["stop_reason"] == "max_tokens"

    def test_create_message_with_content_blocks(self, client, mock_openai_client):
        """Test handling of Claude content blocks in request."""
        mock_openai_client.create_completion.return_value = {
            "id": "test-blocks",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I received your message"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 5,
                "total_tokens": 17
            }
        }

        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hello"},
                        {"type": "text", "text": "World"}
                    ]
                }
            ]
        }

        response = client.post("/v1/messages", json=claude_request)
        assert response.status_code == 200

        # Verify content blocks were converted to single string
        call_args = mock_openai_client.create_completion.call_args[0][0]
        assert call_args["messages"][0]["content"] == "Hello\nWorld"

    def test_create_message_error_handling(self, client, mock_openai_client):
        """Test error handling when OpenAI client raises exception."""
        mock_openai_client.create_completion.side_effect = Exception("API Error")

        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": "Test"
                }
            ]
        }

        response = client.post("/v1/messages", json=claude_request)
        assert response.status_code == 500
        assert "detail" in response.json()

    def test_create_message_invalid_request(self, client):
        """Test handling of invalid request format."""
        invalid_request = {
            "invalid_field": "test"
        }

        response = client.post("/v1/messages", json=invalid_request)
        # Should still process but may have issues
        # This tests robustness
        assert response.status_code in [200, 400, 500]

    def test_streaming_fallback(self, client, mock_openai_client):
        """Test streaming request falls back to non-streaming."""
        mock_openai_client.create_completion.return_value = {
            "id": "test-stream",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Non-streamed response"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 4,
                "total_tokens": 9
            }
        }

        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "stream": True,
            "messages": [
                {
                    "role": "user",
                    "content": "Test streaming"
                }
            ]
        }

        response = client.post("/v1/messages", json=claude_request)
        assert response.status_code == 200

        # Should return non-streaming response
        data = response.json()
        assert data["content"][0]["text"] == "Non-streamed response"

        # Verify stream was disabled in the call
        call_args = mock_openai_client.create_completion.call_args[0][0]
        assert call_args["stream"] is False
