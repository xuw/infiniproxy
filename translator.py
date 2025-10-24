"""Translation logic between Claude and OpenAI API formats."""

from typing import Any, Dict, List, Optional, Union
import json
import time
import uuid


class APITranslator:
    """Translates between Claude and OpenAI API formats."""

    def __init__(self, openai_model: str, max_input_tokens: int = 409600, max_output_tokens: int = 409600):
        """Initialize translator with OpenAI model name and token limits."""
        self.openai_model = openai_model
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens

    def translate_request_to_openai(self, claude_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate Claude API request to OpenAI API request.

        Args:
            claude_request: Request in Claude API format

        Returns:
            Request in OpenAI API format
        """
        openai_request = {
            "model": self.openai_model,
            "messages": [],
        }

        # Handle system message - Claude has separate 'system' field
        if "system" in claude_request:
            system_content = claude_request["system"]
            if isinstance(system_content, list):
                # Handle system as content blocks
                system_text = self._extract_text_from_content_blocks(system_content)
            else:
                system_text = system_content

            openai_request["messages"].append({
                "role": "system",
                "content": system_text
            })

        # Convert messages
        for message in claude_request.get("messages", []):
            openai_messages = self._convert_message_to_openai(message)
            # Handle both single message and list of messages (for tool results)
            if isinstance(openai_messages, list):
                openai_request["messages"].extend(openai_messages)
            else:
                openai_request["messages"].append(openai_messages)

        # Handle tool definitions - translate Claude tools to OpenAI format
        if "tools" in claude_request:
            openai_request["tools"] = self._translate_tools_to_openai(claude_request["tools"])

        # Copy optional parameters with token limit enforcement
        if "max_tokens" in claude_request:
            # Use the smaller of requested tokens and configured max output tokens
            openai_request["max_tokens"] = min(claude_request["max_tokens"], self.max_output_tokens)
        else:
            # Set default max tokens
            openai_request["max_tokens"] = self.max_output_tokens

        if "temperature" in claude_request:
            openai_request["temperature"] = claude_request["temperature"]

        if "top_p" in claude_request:
            openai_request["top_p"] = claude_request["top_p"]

        # Always force non-streaming on OpenAI side
        # Streaming is not implemented for OpenAI backend
        openai_request["stream"] = False

        if "stop_sequences" in claude_request:
            openai_request["stop"] = claude_request["stop_sequences"]

        return openai_request

    def translate_response_to_claude(
        self,
        openai_response: Dict[str, Any],
        original_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Translate OpenAI API response to Claude API response.

        Args:
            openai_response: Response in OpenAI API format
            original_model: Original Claude model name from request

        Returns:
            Response in Claude API format
        """
        # Extract the first choice (Claude doesn't support multiple choices)
        choice = openai_response.get("choices", [{}])[0]
        message = choice.get("message", {})
        content_text = message.get("content", "")

        # Build content blocks
        content_blocks = []

        # Check for reasoning_content (specific to glm-4.6)
        reasoning_content = message.get("reasoning_content", "")
        if reasoning_content:
            # Prepend reasoning to content
            content_text = f"[Reasoning]\n{reasoning_content}\n\n[Response]\n{content_text}"

        # Add text content if present
        if content_text:
            content_blocks.append({
                "type": "text",
                "text": content_text
            })

        # Handle tool calls - translate to Claude tool_use format
        tool_calls = message.get("tool_calls", [])
        if tool_calls:
            for tool_call in tool_calls:
                if tool_call.get("type") == "function":
                    function = tool_call.get("function", {})
                    # Parse arguments JSON string to dict
                    try:
                        arguments = json.loads(function.get("arguments", "{}"))
                    except json.JSONDecodeError:
                        arguments = {}

                    content_blocks.append({
                        "type": "tool_use",
                        "id": tool_call.get("id"),
                        "name": function.get("name"),
                        "input": arguments
                    })

        # Build Claude response
        claude_response = {
            "id": openai_response.get("id", f"msg_{uuid.uuid4().hex[:24]}"),
            "type": "message",
            "role": "assistant",
            "content": content_blocks,
            "model": original_model or self.openai_model,
            "stop_reason": self._map_finish_reason(choice.get("finish_reason")),
        }

        # Add usage information
        if "usage" in openai_response:
            usage = openai_response["usage"]
            claude_response["usage"] = {
                "input_tokens": usage.get("prompt_tokens", 0),
                "output_tokens": usage.get("completion_tokens", 0),
            }

        return claude_response

    def _convert_message_to_openai(self, claude_message: Dict[str, Any]):
        """
        Convert a single Claude message to OpenAI format.

        Returns either a single message dict or a list of messages (for tool results).
        """
        role = claude_message["role"]
        content = claude_message.get("content", "")

        # Handle content - can be string or list of content blocks
        if isinstance(content, list):
            # Check for tool_result blocks - need special handling
            tool_results = [block for block in content if block.get("type") == "tool_result"]

            if tool_results:
                # For tool results, we need to create separate messages for OpenAI
                # First, add any text content as an assistant message
                text_blocks = [block for block in content if block.get("type") == "text"]
                tool_use_blocks = [block for block in content if block.get("type") == "tool_use"]

                messages = []

                # If there's an assistant message with tool_use, add it first
                if role == "assistant" and tool_use_blocks:
                    # This shouldn't happen in user messages, but handle defensively
                    pass

                # Add tool result messages
                for tool_result in tool_results:
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_result.get("tool_use_id"),
                        "content": self._extract_tool_result_content(tool_result.get("content", ""))
                    }
                    messages.append(tool_message)

                # If there's text content alongside tool results, add it as a user message after
                if text_blocks:
                    text_content = "\n".join([block.get("text", "") for block in text_blocks])
                    if text_content.strip():
                        messages.append({
                            "role": "user",
                            "content": text_content
                        })

                return messages if len(messages) > 1 else messages[0] if messages else {"role": role, "content": ""}

            else:
                # No tool results - extract text normally
                openai_message = {
                    "role": role,
                    "content": self._extract_text_from_content_blocks(content)
                }
                return openai_message
        else:
            # Simple string content
            return {
                "role": role,
                "content": content
            }

    def _extract_text_from_content_blocks(self, content_blocks: List[Dict[str, Any]]) -> str:
        """Extract text content from Claude's content blocks."""
        text_parts = []
        for block in content_blocks:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                # Handle tool use blocks if needed
                pass
            # Image blocks would need special handling - for now, skip

        return "\n".join(text_parts)

    def _map_finish_reason(self, openai_finish_reason: Optional[str]) -> str:
        """Map OpenAI finish_reason to Claude stop_reason."""
        mapping = {
            "stop": "end_turn",
            "length": "max_tokens",
            "content_filter": "content_filtered",
            "tool_calls": "tool_use",
            "function_call": "tool_use",
        }
        return mapping.get(openai_finish_reason, "end_turn")

    def _translate_tools_to_openai(self, claude_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Translate Claude tool definitions to OpenAI function format.

        Claude format:
        {
            "name": "get_weather",
            "description": "Get weather info",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }

        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather info",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        }
        """
        openai_tools = []
        for claude_tool in claude_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": claude_tool.get("name"),
                    "description": claude_tool.get("description", ""),
                    "parameters": claude_tool.get("input_schema", {})
                }
            }
            openai_tools.append(openai_tool)
        return openai_tools

    def _extract_tool_result_content(self, content) -> str:
        """
        Extract content from a tool_result.

        Content can be a string or a list of content blocks.
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Extract text from content blocks
            return self._extract_text_from_content_blocks(content)
        else:
            return str(content)
