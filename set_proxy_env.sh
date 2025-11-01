#!/bin/bash
# InfiniProxy Environment Configuration Script
#
# This script configures environment variables to redirect API clients
# to use the InfiniProxy server instead of original API endpoints.
#
# Required Environment Variables:
#   AIAPI_URL - Proxy server URL (e.g., http://localhost:8000)
#   AIAPI_KEY - Proxy API key
#
# Usage:
#   export AIAPI_URL=http://localhost:8000
#   export AIAPI_KEY=your-api-key-here
#   source set_proxy_env.sh
#
# Example:
#   export AIAPI_URL=http://localhost:8000
#   export AIAPI_KEY=sk-abc123...
#   source set_proxy_env.sh

# Configuration from environment variables
PROXY_URL="${AIAPI_URL:-http://localhost:8000}"
PROXY_API_KEY="${AIAPI_KEY}"

# Check if API key is set
if [ -z "$PROXY_API_KEY" ]; then
    echo "❌ Error: AIAPI_KEY environment variable is not set"
    echo ""
    echo "Please set your API key:"
    echo "  export AIAPI_KEY=your-api-key-here"
    echo "  source set_proxy_env.sh"
    return 1 2>/dev/null || exit 1
fi

echo "=================================================="
echo "🚀 InfiniProxy Environment Configuration"
echo "=================================================="
echo "Proxy URL: $PROXY_URL"
echo "API Key:   ${PROXY_API_KEY:0:20}..."
echo ""

# ============================================================================
# OpenAI Configuration
# ============================================================================
export OPENAI_API_BASE="${PROXY_URL}/v1"
export OPENAI_BASE_URL="${PROXY_URL}/v1"
export OPENAI_API_KEY="$PROXY_API_KEY"

echo "✅ OpenAI:"
echo "   OPENAI_API_BASE=$OPENAI_API_BASE"
echo "   OPENAI_BASE_URL=$OPENAI_BASE_URL"
echo "   OPENAI_API_KEY=${OPENAI_API_KEY:0:20}..."

# ============================================================================
# Anthropic/Claude Configuration
# ============================================================================
export ANTHROPIC_BASE_URL="${PROXY_URL}/v1"
export ANTHROPIC_API_URL="${PROXY_URL}/v1"
export ANTHROPIC_API_KEY="$PROXY_API_KEY"

echo ""
echo "✅ Anthropic/Claude:"
echo "   ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"
echo "   ANTHROPIC_API_URL=$ANTHROPIC_API_URL"
echo "   ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:0:20}..."

# ============================================================================
# Firecrawl Configuration
# ============================================================================
export FIRECRAWL_BASE_URL="${PROXY_URL}/v1/firecrawl"
export FIRECRAWL_API_URL="${PROXY_URL}/v1/firecrawl"
export FIRECRAWL_API_KEY="$PROXY_API_KEY"

echo ""
echo "✅ Firecrawl:"
echo "   FIRECRAWL_BASE_URL=$FIRECRAWL_BASE_URL"
echo "   FIRECRAWL_API_KEY=${FIRECRAWL_API_KEY:0:20}..."

# ============================================================================
# ElevenLabs Configuration
# ============================================================================
export ELEVENLABS_API_BASE="${PROXY_URL}/v1/elevenlabs"
export ELEVENLABS_BASE_URL="${PROXY_URL}/v1/elevenlabs"
export ELEVEN_API_KEY="$PROXY_API_KEY"
export ELEVENLABS_API_KEY="$PROXY_API_KEY"

echo ""
echo "✅ ElevenLabs:"
echo "   ELEVENLABS_API_BASE=$ELEVENLABS_API_BASE"
echo "   ELEVENLABS_BASE_URL=$ELEVENLABS_BASE_URL"
echo "   ELEVEN_API_KEY=${ELEVEN_API_KEY:0:20}..."

# ============================================================================
# Tavily Configuration
# ============================================================================
export TAVILY_API_BASE="${PROXY_URL}/v1/tavily"
export TAVILY_BASE_URL="${PROXY_URL}/v1/tavily"
export TAVILY_API_KEY="$PROXY_API_KEY"

echo ""
echo "✅ Tavily:"
echo "   TAVILY_API_BASE=$TAVILY_API_BASE"
echo "   TAVILY_BASE_URL=$TAVILY_BASE_URL"
echo "   TAVILY_API_KEY=${TAVILY_API_KEY:0:20}..."

# ============================================================================
# SerpAPI Configuration
# ============================================================================
export SERPAPI_BASE_URL="${PROXY_URL}/v1/serpapi"
export SERPAPI_API_KEY="$PROXY_API_KEY"

echo ""
echo "✅ SerpAPI:"
echo "   SERPAPI_BASE_URL=$SERPAPI_BASE_URL"
echo "   SERPAPI_API_KEY=${SERPAPI_API_KEY:0:20}..."

# ============================================================================
# Generic Proxy Configuration (for manual use)
# ============================================================================
export INFINIPROXY_URL="$PROXY_URL"
export INFINIPROXY_API_KEY="$PROXY_API_KEY"

echo ""
echo "✅ Generic Proxy:"
echo "   INFINIPROXY_URL=$INFINIPROXY_URL"
echo "   INFINIPROXY_API_KEY=${INFINIPROXY_API_KEY:0:20}..."

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=================================================="
echo "✅ Environment configured successfully!"
echo "=================================================="
echo ""
echo "All API clients should now use the proxy at:"
echo "  $PROXY_URL"
echo ""
echo "To restore original settings, restart your shell or run:"
echo "  source unset_proxy_env.sh"
echo ""
echo "Test the configuration:"
echo "  curl \$OPENAI_API_BASE/models -H \"Authorization: Bearer \$OPENAI_API_KEY\""
echo "=================================================="
