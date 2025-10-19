#!/usr/bin/env python3
"""Test tool calling functionality in the proxy server."""

import requests
import json
import os

# Load environment variables from .env if present
from dotenv import load_dotenv
load_dotenv()

PROXY_URL = "http://localhost:8000"


def test_tool_calling_weather():
    """Test tool calling with a weather function."""

    # Define a simple weather tool
    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather in a given location",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "The unit of temperature"
                    }
                },
                "required": ["location"]
            }
        }
    ]

    # First request - Claude should request to use the tool
    claude_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": tools,
        "messages": [
            {
                "role": "user",
                "content": "What's the weather like in San Francisco?"
            }
        ]
    }

    print("\n" + "=" * 80)
    print("TEST: Tool Calling - Weather Function")
    print("=" * 80)

    print("\n📤 Step 1: Sending request with tool definition...")
    print(f"Tools defined: {json.dumps(tools, indent=2)}")

    response = requests.post(
        f"{PROXY_URL}/v1/messages",
        json=claude_request,
        timeout=30
    )

    print(f"✅ Response status: {response.status_code}")

    if response.status_code != 200:
        print(f"\n❌ Error: {response.text}")
        raise AssertionError(f"Request failed with status {response.status_code}")

    data = response.json()
    print(f"\n📥 Claude Response:")
    print(json.dumps(data, indent=2))

    # Verify response structure
    assert data["type"] == "message"
    assert data["role"] == "assistant"
    assert len(data["content"]) > 0

    # Check if Claude requested to use the tool
    tool_use_blocks = [block for block in data["content"] if block.get("type") == "tool_use"]

    if not tool_use_blocks:
        print("\n⚠️  Warning: Claude did not request to use any tools")
        print("This might be okay - the model may have chosen to answer directly")
        return

    print(f"\n✅ Tool use detected: {len(tool_use_blocks)} tool(s) requested")

    tool_use = tool_use_blocks[0]
    print(f"\n🔧 Tool requested:")
    print(f"  Name: {tool_use['name']}")
    print(f"  ID: {tool_use['id']}")
    print(f"  Input: {json.dumps(tool_use['input'], indent=2)}")

    # Simulate executing the tool and getting a result
    tool_result = "The weather in San Francisco is 18°C (64°F), partly cloudy with light wind."

    # Second request - Send tool result back
    print(f"\n📤 Step 2: Sending tool result back...")
    print(f"Tool result: {tool_result}")

    claude_request_2 = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": tools,
        "messages": [
            {
                "role": "user",
                "content": "What's the weather like in San Francisco?"
            },
            {
                "role": "assistant",
                "content": data["content"]  # Previous assistant response with tool_use
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use["id"],
                        "content": tool_result
                    }
                ]
            }
        ]
    }

    response2 = requests.post(
        f"{PROXY_URL}/v1/messages",
        json=claude_request_2,
        timeout=30
    )

    print(f"✅ Response status: {response2.status_code}")

    if response2.status_code != 200:
        print(f"\n❌ Error: {response2.text}")
        raise AssertionError(f"Request failed with status {response2.status_code}")

    data2 = response2.json()
    print(f"\n📥 Final Claude Response:")
    print(json.dumps(data2, indent=2))

    # Extract final text response
    text_blocks = [block for block in data2["content"] if block.get("type") == "text"]
    if text_blocks:
        print(f"\n💬 Assistant says: {text_blocks[0]['text']}")

    print("\n✅ Tool calling test completed successfully!")


def test_tool_calling_calculator():
    """Test tool calling with a calculator function."""

    tools = [
        {
            "name": "calculate",
            "description": "Perform a mathematical calculation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["add", "subtract", "multiply", "divide"],
                        "description": "The operation to perform"
                    },
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["operation", "a", "b"]
            }
        }
    ]

    claude_request = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "tools": tools,
        "messages": [
            {
                "role": "user",
                "content": "What is 15 multiplied by 24?"
            }
        ]
    }

    print("\n" + "=" * 80)
    print("TEST: Tool Calling - Calculator Function")
    print("=" * 80)

    print("\n📤 Sending request with calculator tool...")

    response = requests.post(
        f"{PROXY_URL}/v1/messages",
        json=claude_request,
        timeout=30
    )

    print(f"✅ Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\n📥 Response:")
        print(json.dumps(data, indent=2))

        # Check for tool use
        tool_use_blocks = [block for block in data["content"] if block.get("type") == "tool_use"]

        if tool_use_blocks:
            print(f"\n✅ Calculator tool requested successfully!")
            tool_use = tool_use_blocks[0]
            print(f"  Operation: {tool_use['input'].get('operation')}")
            print(f"  Values: {tool_use['input'].get('a')} and {tool_use['input'].get('b')}")
        else:
            print("\n⚠️  Note: Model answered directly without using the calculator tool")
    else:
        print(f"\n❌ Error: {response.text}")
        raise AssertionError(f"Request failed with status {response.status_code}")


if __name__ == "__main__":
    print("=" * 80)
    print("OpenAI to Claude Proxy - Tool Calling Tests")
    print("=" * 80)
    print(f"\n⚠️  Make sure the proxy server is running on {PROXY_URL}")
    print("   Run: python proxy_server.py")
    print()

    try:
        # Test weather function
        test_tool_calling_weather()

        # Test calculator function
        test_tool_calling_calculator()

        print("\n" + "=" * 80)
        print("✅ All tool calling tests completed!")
        print("=" * 80)

    except requests.ConnectionError:
        print("\n❌ Error: Could not connect to proxy server")
        print(f"   Make sure the server is running on {PROXY_URL}")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
