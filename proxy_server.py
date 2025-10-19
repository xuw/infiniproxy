"""Main proxy server for translating between Claude and OpenAI APIs."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging
import sys
import time
import json
import os
from typing import Dict, Any

from config import ProxyConfig
from translator import APITranslator
from openai_client import OpenAIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OpenAI to Claude API Proxy",
    description="Proxy server that translates between OpenAI and Claude API formats",
    version="1.0.0"
)

# Global configuration (will be set on startup)
config: ProxyConfig = None
translator: APITranslator = None
openai_client: OpenAIClient = None


@app.on_event("startup")
async def startup_event():
    """Initialize the proxy on startup."""
    global config, translator, openai_client

    logger.info("Starting OpenAI to Claude API Proxy...")

    # Load configuration
    config = ProxyConfig.from_env()
    if config.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize components
    translator = APITranslator(
        config.openai_model,
        config.max_input_tokens,
        config.max_output_tokens
    )
    openai_client = OpenAIClient(
        config.openai_base_url,
        config.openai_api_key,
        config.timeout
    )

    logger.info(f"Proxy server initialized successfully")
    logger.info(f"OpenAI backend: {config.openai_base_url}")
    logger.info(f"OpenAI model: {config.openai_model}")
    logger.info(f"Max input tokens: {config.max_input_tokens}")
    logger.info(f"Max output tokens: {config.max_output_tokens}")
    logger.info(f"Proxy listening on: {config.proxy_host}:{config.proxy_port}")


@app.get("/")
async def root():
    """Root endpoint returning server information."""
    return {
        "name": "OpenAI to Claude API Proxy",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "messages": "/v1/messages",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "pid": os.getpid(),
        "openai_backend": config.openai_base_url,
        "openai_model": config.openai_model
    }


@app.post("/v1/messages")
async def create_message(request: Request):
    """
    Create a message (Claude API endpoint).

    This endpoint accepts Claude API format requests and returns Claude format responses.
    """
    start_time = time.time()
    request_id = None

    try:
        # Parse Claude request
        claude_request = await request.json()

        # Log incoming request details
        original_model = claude_request.get("model", "claude-3-5-sonnet-20241022")
        max_tokens = claude_request.get("max_tokens", config.max_output_tokens)
        is_streaming_requested = claude_request.get("stream", False)

        logger.info("=" * 80)
        logger.info(f"📥 INCOMING REQUEST")
        logger.info(f"Model: {original_model}")
        logger.info(f"Max tokens: {max_tokens}")
        logger.info(f"Streaming requested: {is_streaming_requested}")
        if is_streaming_requested:
            logger.info(f"⚠️  Note: Streaming not supported on OpenAI side, using non-streaming")
        logger.info(f"Temperature: {claude_request.get('temperature', 'default')}")

        # Log message count and preview
        messages = claude_request.get("messages", [])
        logger.info(f"Message count: {len(messages)}")
        if messages:
            last_message = messages[-1]
            content = last_message.get("content", "")
            if isinstance(content, list):
                content = " ".join([b.get("text", "") for b in content if b.get("type") == "text"])
            preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"Last message preview: {preview}")

        logger.debug(f"Full Claude request: {json.dumps(claude_request, indent=2)}")

        # Translate to OpenAI format (will always use non-streaming)
        openai_request = translator.translate_request_to_openai(claude_request)
        logger.debug(f"Translated to OpenAI request: {json.dumps(openai_request, indent=2)}")

        # Always use non-streaming on OpenAI side
        logger.info("🔄 Processing non-streaming request...")
        openai_response = openai_client.create_completion(openai_request)
        request_id = openai_response.get("id")

        logger.debug(f"OpenAI response: {json.dumps(openai_response, indent=2)}")

        # Translate back to Claude format
        claude_response = translator.translate_response_to_claude(
            openai_response,
            original_model
        )

        # Log response details
        elapsed_time = time.time() - start_time
        usage = claude_response.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        stop_reason = claude_response.get("stop_reason", "unknown")

        logger.info(f"✅ REQUEST COMPLETED")
        logger.info(f"Request ID: {request_id}")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Input tokens: {input_tokens}")
        logger.info(f"Output tokens: {output_tokens}")
        logger.info(f"Total tokens: {input_tokens + output_tokens}")
        logger.info(f"Stop reason: {stop_reason}")

        # Log response preview
        content_blocks = claude_response.get("content", [])
        if content_blocks:
            text = content_blocks[0].get("text", "")
            preview = text[:200] + "..." if len(text) > 200 else text
            logger.info(f"Response preview: {preview}")

        logger.debug(f"Full Claude response: {json.dumps(claude_response, indent=2)}")
        logger.info("=" * 80)

        return JSONResponse(content=claude_response)

    except ValueError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ VALIDATION ERROR")
        logger.error(f"Request ID: {request_id}")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Request ID: {request_id}")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full traceback:", exc_info=True)
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Load config to get port
    config = ProxyConfig.from_env()

    uvicorn.run(
        app,
        host=config.proxy_host,
        port=config.proxy_port,
        log_level="info"
    )
