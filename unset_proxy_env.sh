#!/bin/bash
# InfiniProxy Environment Cleanup Script
#
# This script unsets all environment variables set by set_proxy_env.sh
# to restore original API endpoint configurations.
#
# Usage:
#   source unset_proxy_env.sh

echo "=================================================="
echo "🧹 Cleaning InfiniProxy Environment Variables"
echo "=================================================="

# OpenAI
unset OPENAI_API_BASE
unset OPENAI_BASE_URL
unset OPENAI_API_KEY
echo "✅ Unset OpenAI variables"

# Anthropic/Claude
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_API_URL
unset ANTHROPIC_API_KEY
echo "✅ Unset Anthropic/Claude variables"

# Firecrawl
unset FIRECRAWL_BASE_URL
unset FIRECRAWL_API_URL
unset FIRECRAWL_API_KEY
echo "✅ Unset Firecrawl variables"

# ElevenLabs
unset ELEVENLABS_API_BASE
unset ELEVENLABS_BASE_URL
unset ELEVEN_API_KEY
unset ELEVENLABS_API_KEY
echo "✅ Unset ElevenLabs variables"

# Tavily
unset TAVILY_API_BASE
unset TAVILY_BASE_URL
unset TAVILY_API_KEY
echo "✅ Unset Tavily variables"

# SerpAPI
unset SERPAPI_BASE_URL
unset SERPAPI_API_KEY
echo "✅ Unset SerpAPI variables"

# Generic Proxy
unset INFINIPROXY_URL
unset INFINIPROXY_API_KEY
echo "✅ Unset Generic Proxy variables"

echo ""
echo "=================================================="
echo "✅ Environment cleaned successfully!"
echo "=================================================="
echo ""
echo "All proxy environment variables have been removed."
echo "API clients will now use their default endpoints."
echo "=================================================="
