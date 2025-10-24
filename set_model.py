#!/usr/bin/env python3
"""Client script to set model for an API key."""

import os
import sys
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Default base URL
DEFAULT_BASE_URL = "https://aiapi.iiis.co:9443"


def load_api_key(env_file=".env"):
    """Load API key from .env file."""
    # Try to find .env file
    env_path = Path(env_file)

    if not env_path.exists():
        # Try in parent directory
        env_path = Path(__file__).parent / env_file

    if not env_path.exists():
        print(f"❌ Error: {env_file} file not found")
        print(f"   Searched in: {Path.cwd()} and {Path(__file__).parent}")
        return None

    # Load environment variables
    load_dotenv(env_path)

    # Try different common environment variable names
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('API_KEY') or os.getenv('ANTHROPIC_API_KEY')

    if not api_key:
        print(f"❌ Error: No API key found in {env_file}")
        print("   Expected one of: OPENAI_API_KEY, API_KEY, or ANTHROPIC_API_KEY")
        return None

    print(f"✅ Loaded API key from {env_path}: {api_key[:20]}...")
    return api_key


def get_current_model(base_url, api_key):
    """Get the current model setting."""
    try:
        response = requests.get(
            f"{base_url}/settings/model",
            headers={"Authorization": f"Bearer {api_key}"},
            verify=False
        )

        if response.status_code == 200:
            data = response.json()
            model = data.get('model_name')
            using_default = data.get('using_default', False)

            if using_default or model is None:
                print(f"📋 Current model: Default (global setting)")
            else:
                print(f"📋 Current model: {model}")

            return data
        else:
            print(f"❌ Failed to get current model: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error getting current model: {e}")
        return None


def list_backend_models(base_url, api_key):
    """List all models available from the backend via proxy."""
    try:
        models_url = f"{base_url}/v1/models"

        print(f"🔍 Querying models from proxy: {models_url}")
        print()

        # Query the proxy's models endpoint
        models_response = requests.get(
            models_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            verify=False,
            timeout=10
        )

        if models_response.status_code == 200:
            data = models_response.json()

            # Handle different response formats
            if 'data' in data:
                models = data['data']
            elif 'models' in data:
                models = data['models']
            elif isinstance(data, list):
                models = data
            else:
                models = [data]

            print("📋 Available Models:")
            print("=" * 80)

            if not models:
                print("No models found")
                return []

            # Display models
            for i, model in enumerate(models, 1):
                if isinstance(model, dict):
                    model_id = model.get('id') or model.get('model') or model.get('name', 'Unknown')
                    created = model.get('created', '')
                    owned_by = model.get('owned_by', '')

                    print(f"{i}. {model_id}")
                    if created:
                        print(f"   Created: {created}")
                    if owned_by:
                        print(f"   Owner: {owned_by}")
                    print()
                else:
                    print(f"{i}. {model}")
                    print()

            return models
        else:
            print(f"❌ Failed to list models: {models_response.status_code}")
            print(f"   Response: {models_response.text}")
            return None

    except requests.exceptions.Timeout:
        print(f"❌ Request timeout while fetching models")
        return None
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return None


def set_model(base_url, api_key, model_name):
    """Set the model for the API key."""
    try:
        response = requests.put(
            f"{base_url}/settings/model",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"model_name": model_name},
            verify=False
        )

        if response.status_code == 200:
            data = response.json()
            if model_name is None:
                print(f"✅ Model unset successfully, using default global model")
            else:
                print(f"✅ Model set successfully to: {model_name}")
            return True
        else:
            print(f"❌ Failed to set model: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error setting model: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Set model for an API key",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available models from backend
  python set_model.py --list-models

  # Set model to gpt-4
  python set_model.py gpt-4

  # Set model to claude-3-5-sonnet
  python set_model.py claude-3-5-sonnet-20241022

  # Unset model (use default)
  python set_model.py --unset

  # Just check current model
  python set_model.py --check

  # Use different .env file
  python set_model.py --env-file .env.production gpt-4

  # Use different base URL
  python set_model.py --url https://different-url.com gpt-4
        """
    )

    parser.add_argument(
        'model',
        nargs='?',
        help='Model name to set (e.g., gpt-4, claude-3-opus, glm-4.6)'
    )

    parser.add_argument(
        '--unset',
        action='store_true',
        help='Unset the model (use default global model)'
    )

    parser.add_argument(
        '--check',
        action='store_true',
        help='Just check the current model setting'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List all models available from the backend'
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

    args = parser.parse_args()

    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    print("="*80)
    print("InfiniProxy Model Settings Client")
    print("="*80)
    print()

    # Load API key
    api_key = load_api_key(args.env_file)
    if not api_key:
        return 1

    print(f"🌐 Base URL: {args.url}")
    print()

    # Check current model
    current = get_current_model(args.url, api_key)

    if args.check:
        # Just checking, exit
        return 0 if current else 1

    if args.list_models:
        # List available models from backend via proxy
        print()
        models = list_backend_models(args.url, api_key)
        print()
        print("="*80)
        if models is not None:
            print(f"✅ Found {len(models)} models")
        else:
            print("❌ Failed to list models")
        print("="*80)
        return 0 if models is not None else 1

    # Determine what to do
    if args.unset:
        model_name = None
        print()
        print("🔄 Unsetting model (will use default)...")
    elif args.model:
        model_name = args.model
        print()
        print(f"🔄 Setting model to: {model_name}...")
    else:
        print()
        print("ℹ️  No action specified. Use --unset to unset or provide a model name.")
        print("   Use --help for more information.")
        return 0

    # Set the model
    success = set_model(args.url, api_key, model_name)

    if success:
        print()
        print("🔍 Verifying change...")
        get_current_model(args.url, api_key)
        print()
        print("="*80)
        print("✅ Done!")
        print("="*80)
        return 0
    else:
        print()
        print("="*80)
        print("❌ Failed!")
        print("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
