"""Unit tests for the API translator."""

import pytest
from translator import APITranslator


class TestAPITranslator:
    """Test cases for APITranslator class."""

    @pytest.fixture
    def translator(self):
        """Create a translator instance for testing."""
        return APITranslator(openai_model="glm-4.6")

    def test_translate_simple_request(self, translator):
        """Test translation of a simple Claude request to OpenAI format."""
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, how are you?"
                }
            ]
        }

        openai_request = translator.translate_request_to_openai(claude_request)

        assert openai_request["model"] == "glm-4.6"
        assert openai_request["max_tokens"] == 1024
        assert len(openai_request["messages"]) == 1
        assert openai_request["messages"][0]["role"] == "user"
        assert openai_request["messages"][0]["content"] == "Hello, how are you?"

    def test_translate_request_with_system(self, translator):
        """Test translation of request with system message."""
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "system": "You are a helpful assistant.",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello!"
                }
            ]
        }

        openai_request = translator.translate_request_to_openai(claude_request)

        assert len(openai_request["messages"]) == 2
        assert openai_request["messages"][0]["role"] == "system"
        assert openai_request["messages"][0]["content"] == "You are a helpful assistant."
        assert openai_request["messages"][1]["role"] == "user"
        assert openai_request["messages"][1]["content"] == "Hello!"

    def test_translate_request_with_content_blocks(self, translator):
        """Test translation of request with Claude content blocks."""
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Hello!"},
                        {"type": "text", "text": "How are you?"}
                    ]
                }
            ]
        }

        openai_request = translator.translate_request_to_openai(claude_request)

        assert openai_request["messages"][0]["content"] == "Hello!\nHow are you?"

    def test_translate_request_with_temperature(self, translator):
        """Test translation preserves temperature parameter."""
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.8,
            "messages": [{"role": "user", "content": "Test"}]
        }

        openai_request = translator.translate_request_to_openai(claude_request)

        assert openai_request["temperature"] == 0.8

    def test_translate_request_with_stop_sequences(self, translator):
        """Test translation of stop_sequences to stop parameter."""
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "stop_sequences": ["END", "STOP"],
            "messages": [{"role": "user", "content": "Test"}]
        }

        openai_request = translator.translate_request_to_openai(claude_request)

        assert openai_request["stop"] == ["END", "STOP"]

    def test_translate_simple_response(self, translator):
        """Test translation of OpenAI response to Claude format."""
        openai_response = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677652288,
            "model": "glm-4.6",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! I'm doing well, thank you."
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

        claude_response = translator.translate_response_to_claude(
            openai_response,
            original_model="claude-3-5-sonnet-20241022"
        )

        assert claude_response["id"] == "chatcmpl-123"
        assert claude_response["type"] == "message"
        assert claude_response["role"] == "assistant"
        assert claude_response["model"] == "claude-3-5-sonnet-20241022"
        assert len(claude_response["content"]) == 1
        assert claude_response["content"][0]["type"] == "text"
        assert claude_response["content"][0]["text"] == "Hello! I'm doing well, thank you."
        assert claude_response["stop_reason"] == "end_turn"
        assert claude_response["usage"]["input_tokens"] == 10
        assert claude_response["usage"]["output_tokens"] == 20

    def test_translate_response_with_reasoning(self, translator):
        """Test translation of response with reasoning_content (glm-4.6 specific)."""
        openai_response = {
            "id": "test-123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Final answer here",
                        "reasoning_content": "Let me think step by step..."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 15,
                "total_tokens": 20
            }
        }

        claude_response = translator.translate_response_to_claude(openai_response)

        content_text = claude_response["content"][0]["text"]
        assert "[Reasoning]" in content_text
        assert "Let me think step by step..." in content_text
        assert "[Response]" in content_text
        assert "Final answer here" in content_text

    def test_finish_reason_mapping(self, translator):
        """Test mapping of different finish_reason values."""
        test_cases = [
            ("stop", "end_turn"),
            ("length", "max_tokens"),
            ("content_filter", "content_filtered"),
            ("tool_calls", "tool_use"),
            ("unknown", "end_turn"),  # Default case
        ]

        for openai_reason, expected_claude_reason in test_cases:
            openai_response = {
                "id": "test",
                "choices": [
                    {
                        "message": {"role": "assistant", "content": "Test"},
                        "finish_reason": openai_reason
                    }
                ],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
            }

            claude_response = translator.translate_response_to_claude(openai_response)
            assert claude_response["stop_reason"] == expected_claude_reason

    def test_empty_content_blocks(self, translator):
        """Test handling of empty content blocks."""
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {
                    "role": "user",
                    "content": []
                }
            ]
        }

        openai_request = translator.translate_request_to_openai(claude_request)

        assert openai_request["messages"][0]["content"] == ""

    def test_multi_turn_conversation(self, translator):
        """Test translation of multi-turn conversation."""
        claude_request = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]
        }

        openai_request = translator.translate_request_to_openai(claude_request)

        assert len(openai_request["messages"]) == 3
        assert openai_request["messages"][0]["role"] == "user"
        assert openai_request["messages"][1]["role"] == "assistant"
        assert openai_request["messages"][2]["role"] == "user"

    def test_missing_usage_in_response(self, translator):
        """Test handling of missing usage data in response."""
        openai_response = {
            "id": "test",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Test"},
                    "finish_reason": "stop"
                }
            ]
        }

        claude_response = translator.translate_response_to_claude(openai_response)

        # Should not have usage field if not in original response
        assert "usage" not in claude_response
