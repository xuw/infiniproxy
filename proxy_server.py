"""Main proxy server for translating between Claude and OpenAI APIs."""

from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import logging
import sys
import time
import json
import os
from typing import Dict, Any, Optional

from config import ProxyConfig
from translator import APITranslator
from openai_client import OpenAIClient
from user_manager import UserManager

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

# Mount static files for admin UI
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Global configuration (will be set on startup)
config: ProxyConfig = None
translator: APITranslator = None
openai_client: OpenAIClient = None
user_manager: UserManager = None

# Security
security = HTTPBearer(auto_error=False)


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Dependency to validate API key and get current user.

    Expects Authorization header: Bearer <api-key>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include 'Authorization: Bearer <your-api-key>' header."
        )

    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use 'Bearer <api-key>'"
        )

    api_key = parts[1]

    # Validate API key
    user_info = user_manager.validate_api_key(api_key)
    if not user_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key"
        )

    return user_info


@app.on_event("startup")
async def startup_event():
    """Initialize the proxy on startup."""
    global config, translator, openai_client, user_manager

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

    # Initialize user manager
    user_manager = UserManager()
    logger.info("User manager initialized")

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
            "claude_messages": "/v1/messages (Claude API format)",
            "openai_chat": "/v1/chat/completions (OpenAI API format - pass-through)",
            "health": "/health",
            "admin_ui": "/admin (Web-based admin interface)"
        }
    }


@app.get("/admin", response_class=HTMLResponse)
async def admin_ui():
    """Serve the admin UI."""
    try:
        with open("static/admin.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Admin UI not found")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "pid": os.getpid(),
        "openai_backend": config.openai_base_url,
        "openai_model": config.openai_model
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Chat completions endpoint (OpenAI API format - pass-through).

    This endpoint accepts OpenAI API format requests and passes them directly
    to the backend without translation, returning OpenAI format responses.

    Requires authentication via Bearer token.
    """
    start_time = time.time()
    request_id = None

    try:
        # Parse OpenAI request
        openai_request = await request.json()

        # Log incoming request details
        model = openai_request.get("model", config.openai_model)
        max_tokens = openai_request.get("max_tokens", config.max_output_tokens)
        is_streaming = openai_request.get("stream", False)

        logger.info("=" * 80)
        logger.info(f"📥 INCOMING OPENAI REQUEST (PASS-THROUGH)")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Model: {model}")
        logger.info(f"Max tokens: {max_tokens}")
        logger.info(f"Streaming: {is_streaming}")
        logger.info(f"Temperature: {openai_request.get('temperature', 'default')}")

        # Log message count and preview
        messages = openai_request.get("messages", [])
        logger.info(f"Message count: {len(messages)}")
        if messages:
            last_message = messages[-1]
            content = last_message.get("content", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"Last message preview: {preview}")

        logger.debug(f"Full OpenAI request: {json.dumps(openai_request, indent=2)}")

        # Pass through to OpenAI backend
        logger.info("🔄 Passing through to OpenAI backend...")
        openai_response = openai_client.create_completion(openai_request)
        request_id = openai_response.get("id")

        logger.debug(f"OpenAI response: {json.dumps(openai_response, indent=2)}")

        # Log response details
        elapsed_time = time.time() - start_time
        usage = openai_response.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        logger.info(f"✅ REQUEST COMPLETED")
        logger.info(f"Request ID: {request_id}")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Prompt tokens: {prompt_tokens}")
        logger.info(f"Completion tokens: {completion_tokens}")
        logger.info(f"Total tokens: {prompt_tokens + completion_tokens}")

        # Log response preview
        choices = openai_response.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "")
            preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"Response preview: {preview}")

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/chat/completions',
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            model=model,
            request_id=request_id
        )
        logger.info(f"✅ Usage tracked for user {user_info['username']}")

        logger.info("=" * 80)

        # Return OpenAI format response directly
        return JSONResponse(content=openai_response)

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


@app.post("/v1/messages")
async def create_message(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a message (Claude API endpoint).

    This endpoint accepts Claude API format requests and returns Claude format responses.

    Requires authentication via Bearer token.
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
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
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

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/messages',
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=original_model,
            request_id=request_id
        )
        logger.info(f"✅ Usage tracked for user {user_info['username']}")

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


@app.post("/admin/users")
async def create_user(username: str, email: Optional[str] = None):
    """
    Create a new user.

    Admin endpoint - no authentication required for user creation.
    """
    try:
        user_id = user_manager.create_user(username, email)
        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "message": f"User {username} created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin/api-keys")
async def create_api_key_endpoint(user_id: int, name: Optional[str] = None):
    """
    Create a new API key for a user.

    Admin endpoint - no authentication required for key creation.

    Returns the API key - this is the ONLY time it will be shown!
    """
    try:
        api_key = user_manager.create_api_key(user_id, name)
        return {
            "success": True,
            "api_key": api_key,
            "user_id": user_id,
            "name": name,
            "warning": "Save this API key! It will not be shown again."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/admin/users")
async def list_users_endpoint():
    """
    List all users.

    Admin endpoint.
    """
    users = user_manager.list_users()
    return {"users": users}


@app.get("/admin/api-keys")
async def list_api_keys_endpoint(user_id: Optional[int] = None):
    """
    List API keys, optionally filtered by user.

    Admin endpoint.
    """
    api_keys = user_manager.list_api_keys(user_id)
    return {"api_keys": api_keys}


@app.delete("/admin/api-keys/{api_key_id}")
async def deactivate_api_key_endpoint(api_key_id: int):
    """
    Deactivate an API key.

    Admin endpoint.
    """
    try:
        user_manager.deactivate_api_key(api_key_id)
        return {
            "success": True,
            "message": f"API key {api_key_id} deactivated"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/usage/me")
async def get_my_usage(
    user_info: Dict[str, Any] = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get usage statistics for the authenticated user.

    Query parameters:
    - start_date: ISO format date (e.g., 2024-01-01T00:00:00)
    - end_date: ISO format date (e.g., 2024-12-31T23:59:59)
    """
    usage = user_manager.get_user_usage(
        user_info['user_id'],
        start_date,
        end_date
    )
    usage['username'] = user_info['username']
    return usage


@app.get("/usage/api-key/{api_key_id}")
async def get_api_key_usage_endpoint(api_key_id: int):
    """
    Get usage statistics for a specific API key.

    Admin endpoint.
    """
    usage = user_manager.get_api_key_usage(api_key_id)
    return usage


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
