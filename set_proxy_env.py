#!/usr/bin/env python3
"""
InfiniProxy Environment Configuration (Python)

This script configures environment variables to redirect API clients
to use the InfiniProxy server instead of original API endpoints.

Required Environment Variables:
    AIAPI_URL - Proxy server URL (e.g., http://localhost:8000)
    AIAPI_KEY - Proxy API key

Usage:
    export AIAPI_URL=http://localhost:8000
    export AIAPI_KEY=your-api-key-here
    python set_proxy_env.py                    # Print summary
    python set_proxy_env.py --export           # Print export statements
    python set_proxy_env.py --json             # Print JSON format

Examples:
    export AIAPI_URL=http://localhost:8000
    export AIAPI_KEY=sk-abc123...
    python set_proxy_env.py
    python set_proxy_env.py --export > /tmp/proxy_env.sh
    source /tmp/proxy_env.sh
"""

import os
import sys
import json


def get_proxy_config():
    """Get proxy configuration from environment variables."""
    proxy_url = os.getenv("AIAPI_URL", "http://localhost:8000")
    proxy_api_key = os.getenv("AIAPI_KEY")

    # Check if API key is set
    if not proxy_api_key:
        print("❌ Error: AIAPI_KEY environment variable is not set", file=sys.stderr)
        print("", file=sys.stderr)
        print("Please set your API key:", file=sys.stderr)
        print("  export AIAPI_KEY=your-api-key-here", file=sys.stderr)
        print("  python set_proxy_env.py", file=sys.stderr)
        sys.exit(1)

    return {
        "proxy_url": proxy_url,
        "proxy_api_key": proxy_api_key,
        "env_vars": {
            # OpenAI
            "OPENAI_API_BASE": f"{proxy_url}/v1",
            "OPENAI_BASE_URL": f"{proxy_url}/v1",
            "OPENAI_API_KEY": proxy_api_key,

            # Anthropic/Claude
            "ANTHROPIC_BASE_URL": f"{proxy_url}/v1",
            "ANTHROPIC_API_URL": f"{proxy_url}/v1",
            "ANTHROPIC_API_KEY": proxy_api_key,

            # Firecrawl
            "FIRECRAWL_BASE_URL": f"{proxy_url}/v1/firecrawl",
            "FIRECRAWL_API_URL": f"{proxy_url}/v1/firecrawl",
            "FIRECRAWL_API_KEY": proxy_api_key,

            # ElevenLabs
            "ELEVENLABS_API_BASE": f"{proxy_url}/v1/elevenlabs",
            "ELEVENLABS_BASE_URL": f"{proxy_url}/v1/elevenlabs",
            "ELEVEN_API_KEY": proxy_api_key,
            "ELEVENLABS_API_KEY": proxy_api_key,

            # Tavily
            "TAVILY_API_BASE": f"{proxy_url}/v1/tavily",
            "TAVILY_BASE_URL": f"{proxy_url}/v1/tavily",
            "TAVILY_API_KEY": proxy_api_key,

            # SerpAPI
            "SERPAPI_BASE_URL": f"{proxy_url}/v1/serpapi",
            "SERPAPI_API_KEY": proxy_api_key,

            # Generic Proxy
            "INFINIPROXY_URL": proxy_url,
            "INFINIPROXY_API_KEY": proxy_api_key,
        }
    }


def set_environment(config):
    """Set environment variables in current Python process."""
    for key, value in config["env_vars"].items():
        os.environ[key] = value


def print_export_statements(config):
    """Print bash export statements."""
    print("# InfiniProxy Environment Configuration")
    print(f"# Proxy URL: {config['proxy_url']}")
    print(f"# API Key: {config['proxy_api_key'][:20]}...")
    print()

    for key, value in config["env_vars"].items():
        print(f'export {key}="{value}"')


def print_summary(config):
    """Print configuration summary."""
    print("=" * 50)
    print("🚀 InfiniProxy Environment Configuration")
    print("=" * 50)
    print(f"Proxy URL: {config['proxy_url']}")
    print(f"API Key:   {config['proxy_api_key'][:20]}...")
    print()

    # Group by service
    services = {
        "OpenAI": ["OPENAI_API_BASE", "OPENAI_BASE_URL"],
        "Anthropic/Claude": ["ANTHROPIC_BASE_URL", "ANTHROPIC_API_URL"],
        "Firecrawl": ["FIRECRAWL_BASE_URL"],
        "ElevenLabs": ["ELEVENLABS_API_BASE", "ELEVENLABS_BASE_URL"],
        "Tavily": ["TAVILY_API_BASE", "TAVILY_BASE_URL"],
        "SerpAPI": ["SERPAPI_BASE_URL"],
    }

    for service, keys in services.items():
        print(f"✅ {service}:")
        for key in keys:
            value = config["env_vars"][key]
            print(f"   {key}={value}")
        print()

    print("=" * 50)
    print("✅ Environment configured successfully!")
    print("=" * 50)
    print()
    print("To export for shell use:")
    print(f"  python {sys.argv[0]} --export > /tmp/proxy_env.sh")
    print("  source /tmp/proxy_env.sh")
    print()
    print("To use in Python code:")
    print("  from set_proxy_env import configure_proxy")
    print("  configure_proxy()")
    print("=" * 50)


def configure_proxy():
    """
    Configure environment for InfiniProxy (for import use).

    Reads configuration from AIAPI_URL and AIAPI_KEY environment variables.

    Returns:
        dict: Configuration with proxy_url, proxy_api_key, and env_vars
    """
    config = get_proxy_config()
    set_environment(config)
    return config


def main():
    """Main entry point."""
    # Parse arguments
    output_format = "summary"

    for arg in sys.argv[1:]:
        if arg == "--export":
            output_format = "export"
        elif arg == "--json":
            output_format = "json"
        elif arg in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)

    # Get configuration
    config = get_proxy_config()

    # Set environment in current process
    set_environment(config)

    # Output based on format
    if output_format == "export":
        print_export_statements(config)
    elif output_format == "json":
        print(json.dumps(config, indent=2))
    else:
        print_summary(config)


if __name__ == "__main__":
    main()
