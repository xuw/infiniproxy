#!/usr/bin/env python3
"""Test client for sending chat messages to InfiniProxy."""

import os
import sys
import argparse
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
import time
import base64
import mimetypes

# Default base URL
DEFAULT_BASE_URL = "https://aiapi.iiis.co:9443"


def encode_file(file_path):
    """Encode a file to base64 and detect its MIME type."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'rb') as f:
        file_data = f.read()

    base64_data = base64.b64encode(file_data).decode('utf-8')
    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

    return base64_data, mime_type


def load_api_key(env_file=".env"):
    """Load API key from .env file."""
    env_path = Path(env_file)

    if not env_path.exists():
        env_path = Path(__file__).parent / env_file

    if not env_path.exists():
        print(f"❌ Error: {env_file} file not found")
        return None

    load_dotenv(env_path)

    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('API_KEY') or os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print(f"❌ Error: No API key found in {env_file}")
        return None

    print(f"✅ Loaded API key: {api_key[:20]}...")
    return api_key


def send_claude_format(base_url, api_key, message, model, max_tokens, stream, files=None):
    """Send message using Claude API format (/v1/messages)."""
    url = f"{base_url}/v1/messages"

    # Build content - can be string or array of content blocks
    if files:
        content = [{"type": "text", "text": message}]
        for file_path in files:
            base64_data, mime_type = encode_file(file_path)
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": base64_data
                }
            })
    else:
        content = message

    payload = {
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": content}
        ]
    }

    if model:
        payload["model"] = model

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if stream:
        payload["stream"] = True
        headers["Accept"] = "text/event-stream"

    print(f"📤 Sending to: {url}")
    print(f"📝 Message: {message}")
    print(f"🤖 Model: {model if model else 'server default'}")
    print(f"⏳ Waiting for response...\n")

    start_time = time.time()

    try:
        if stream:
            response = requests.post(url, json=payload, headers=headers, verify=False, stream=True)

            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False

            print("📥 Response (streaming):")
            print("-" * 80)

            has_reasoning = False
            reasoning_started = False
            content_started = False

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            # Handle both Claude format and OpenAI format streams
                            if data.get('type') == 'content_block_delta':
                                # Claude format
                                delta = data.get('delta', {})
                                if delta.get('type') == 'text_delta':
                                    print(delta.get('text', ''), end='', flush=True)
                            elif 'choices' in data and len(data['choices']) > 0:
                                # OpenAI format (proxy may pass through OpenAI format)
                                delta = data['choices'][0].get('delta', {})

                                # Check for reasoning content
                                reasoning = delta.get('reasoning_content', '')
                                if reasoning:
                                    if not reasoning_started:
                                        print("🤔 Thinking:")
                                        print("-" * 80)
                                        reasoning_started = True
                                        has_reasoning = True
                                    print(reasoning, end='', flush=True)

                                # Check for regular content
                                content = delta.get('content', '')
                                if content:
                                    if has_reasoning and not content_started:
                                        print("\n" + "-" * 80)
                                        print("\n💬 Response:")
                                        print("-" * 80)
                                        content_started = True
                                    print(content, end='', flush=True)
                        except json.JSONDecodeError:
                            pass

            print("\n" + "-" * 80)

        else:
            response = requests.post(url, json=payload, headers=headers, verify=False)

            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False

            data = response.json()

            print("📥 Response:")
            print("-" * 80)

            if 'content' in data and len(data['content']) > 0:
                content = data['content'][0]
                if content.get('type') == 'text':
                    print(content['text'])
            else:
                print(json.dumps(data, indent=2))

            print("-" * 80)

            # Show usage
            if 'usage' in data:
                usage = data['usage']
                print(f"\n📊 Token Usage:")
                print(f"   Input:  {usage.get('input_tokens', 0)}")
                print(f"   Output: {usage.get('output_tokens', 0)}")
                print(f"   Total:  {usage.get('input_tokens', 0) + usage.get('output_tokens', 0)}")

        elapsed = time.time() - start_time
        print(f"\n⏱️  Time: {elapsed:.2f}s")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def send_openai_format(base_url, api_key, message, model, max_tokens, stream, files=None):
    """Send message using OpenAI API format (/v1/chat/completions)."""
    url = f"{base_url}/v1/chat/completions"

    # Build content - can be string or array of content blocks
    if files:
        content = [{"type": "text", "text": message}]
        for file_path in files:
            base64_data, mime_type = encode_file(file_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{base64_data}"
                }
            })
    else:
        content = message

    payload = {
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": content}
        ]
    }

    if model:
        payload["model"] = model

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    if stream:
        payload["stream"] = True

    print(f"📤 Sending to: {url}")
    print(f"📝 Message: {message}")
    print(f"🤖 Model: {model if model else 'server default'}")
    print(f"⏳ Waiting for response...\n")

    start_time = time.time()

    try:
        if stream:
            response = requests.post(url, json=payload, headers=headers, verify=False, stream=True)

            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False

            print("📥 Response (streaming):")
            print("-" * 80)

            has_reasoning = False
            reasoning_started = False
            content_started = False

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})

                                # Check for reasoning content
                                reasoning = delta.get('reasoning_content', '')
                                if reasoning:
                                    if not reasoning_started:
                                        print("🤔 Thinking:")
                                        print("-" * 80)
                                        reasoning_started = True
                                        has_reasoning = True
                                    print(reasoning, end='', flush=True)

                                # Check for regular content
                                content = delta.get('content', '')
                                if content:
                                    if has_reasoning and not content_started:
                                        print("\n" + "-" * 80)
                                        print("\n💬 Response:")
                                        print("-" * 80)
                                        content_started = True
                                    print(content, end='', flush=True)
                        except json.JSONDecodeError:
                            pass

            print("\n" + "-" * 80)

        else:
            response = requests.post(url, json=payload, headers=headers, verify=False)

            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False

            data = response.json()

            print("📥 Response:")
            print("-" * 80)

            if 'choices' in data and len(data['choices']) > 0:
                choice = data['choices'][0]
                message = choice.get('message', {})
                reasoning_content = message.get('reasoning_content', '')
                message_content = message.get('content', '')

                # Show reasoning/thinking first if available
                if reasoning_content:
                    print("🤔 Thinking:")
                    print("-" * 80)
                    print(reasoning_content)
                    print("-" * 80)
                    print()
                    print("💬 Response:")
                    print("-" * 80)

                print(message_content)
            else:
                print(json.dumps(data, indent=2))

            print("-" * 80)

            # Show usage
            if 'usage' in data:
                usage = data['usage']
                print(f"\n📊 Token Usage:")
                print(f"   Prompt:     {usage.get('prompt_tokens', 0)}")
                print(f"   Completion: {usage.get('completion_tokens', 0)}")
                print(f"   Total:      {usage.get('total_tokens', 0)}")

        elapsed = time.time() - start_time
        print(f"\n⏱️  Time: {elapsed:.2f}s")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test chat client for InfiniProxy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple message (OpenAI format, default)
  python test_chat.py "Hello, how are you?"

  # Claude format
  python test_chat.py "Hello!" --format claude

  # Custom model
  python test_chat.py "Explain quantum computing" --model gpt-4

  # More tokens
  python test_chat.py "Write a story" --max-tokens 2000

  # Streaming response
  python test_chat.py "Count to 10" --stream

  # Multi-modal with image
  python test_chat.py "What's in this image?" --files image.jpg

  # Multi-modal with multiple files
  python test_chat.py "Analyze these images" --files img1.jpg img2.png

  # Different server
  python test_chat.py "Test" --url http://localhost:8000

  # Custom .env file
  python test_chat.py "Test" --env-file .env.production
        """
    )

    parser.add_argument(
        'message',
        help='Message to send to the model'
    )

    parser.add_argument(
        '--format',
        choices=['claude', 'openai'],
        default='openai',
        help='API format to use (default: openai)'
    )

    parser.add_argument(
        '--model',
        default=None,
        help='Model name (default: use server per-key or global default)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        default=8192,
        help='Maximum tokens in response (default: 8192)'
    )

    parser.add_argument(
        '--stream',
        action='store_true',
        default=True,
        help='Enable streaming response (default: enabled, use --no-stream to disable)'
    )

    parser.add_argument(
        '--no-stream',
        action='store_false',
        dest='stream',
        help='Disable streaming response'
    )

    parser.add_argument(
        '--env-file',
        default='.env',
        help='Path to .env file (default: .env)'
    )

    parser.add_argument(
        '--url',
        default=DEFAULT_BASE_URL,
        help=f'Base URL of the proxy server (default: {DEFAULT_BASE_URL})'
    )

    parser.add_argument(
        '--files',
        nargs='*',
        help='List of file paths to include (images, PDFs, etc.)'
    )

    args = parser.parse_args()

    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("=" * 80)
    print("InfiniProxy Chat Test Client")
    print("=" * 80)
    print()

    # Load API key
    api_key = load_api_key(args.env_file)
    if not api_key:
        return 1

    print(f"🌐 Base URL: {args.url}")
    print(f"📋 Format: {args.format.upper()}")
    print()

    # Send message
    if args.format == 'claude':
        success = send_claude_format(
            args.url, api_key, args.message, args.model, args.max_tokens, args.stream, args.files
        )
    else:
        success = send_openai_format(
            args.url, api_key, args.message, args.model, args.max_tokens, args.stream, args.files
        )

    print()
    print("=" * 80)
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")
    print("=" * 80)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
