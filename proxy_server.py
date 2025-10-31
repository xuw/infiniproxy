"""Main proxy server for translating between Claude and OpenAI APIs."""

from fastapi import FastAPI, HTTPException, Request, Depends, Header, Cookie, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, HTMLResponse, Response, RedirectResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
import logging
import sys
import time
import json
import os
import csv
import io
import requests
import websockets
import asyncio
from typing import Dict, Any, Optional, List

from config import ProxyConfig
from translator import APITranslator
from openai_client import OpenAIClient
from user_manager import UserManager
from email_sender import EmailSender
from backend_manager import BackendManager
import admin_auth

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
email_sender: EmailSender = None
backend_manager: BackendManager = None

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


async def verify_admin_session(admin_session: Optional[str] = Cookie(None)):
    """
    Dependency to verify admin session token.

    Checks for admin_session cookie and validates it.
    """
    if not admin_session:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required. Please login."
        )

    if not admin_auth.admin_auth.verify_session(admin_session):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please login again."
        )

    return admin_session


@app.on_event("startup")
async def startup_event():
    """Initialize the proxy on startup."""
    global config, translator, openai_client, user_manager, email_sender, backend_manager

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
    # Use /app/data directory if it exists (Docker), otherwise current directory
    db_dir = "/app/data" if os.path.exists("/app/data") else "."
    db_path = os.path.join(db_dir, "proxy_users.db")
    user_manager = UserManager(db_path=db_path)
    logger.info(f"User manager initialized with database at {db_path}")

    # Initialize backend manager for multiple backend services
    backend_manager = BackendManager(db_path=db_path)
    logger.info(f"Backend manager initialized with database at {db_path}")

    # Initialize email sender for API key notifications
    email_sender = EmailSender()
    logger.info("Email sender initialized for API key notifications")

    # Initialize admin authentication with same database
    admin_auth.init_admin_auth(db_path=db_path)
    logger.info(f"Admin authentication initialized with database-backed sessions at {db_path}")

    logger.info(f"Proxy server initialized successfully")
    logger.info(f"OpenAI backend: {config.openai_base_url}")
    logger.info(f"OpenAI model: {config.openai_model}")
    logger.info(f"Max input tokens: {config.max_input_tokens}")
    logger.info(f"Max output tokens: {config.max_output_tokens}")
    logger.info(f"Proxy listening on: {config.proxy_host}:{config.proxy_port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global openai_client
    if openai_client:
        await openai_client.close()
        logger.info("OpenAI client closed")


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
            "firecrawl_scrape": "/v1/firecrawl/scrape (Firecrawl scrape endpoint)",
            "firecrawl_crawl": "/v1/firecrawl/crawl (Firecrawl crawl endpoint)",
            "firecrawl_search": "/v1/firecrawl/search (Firecrawl search endpoint)",
            "firecrawl_status": "/v1/firecrawl/crawl/status/{job_id} (Firecrawl status endpoint)",
            "elevenlabs_tts": "/v1/elevenlabs/text-to-speech (ElevenLabs text-to-speech)",
            "elevenlabs_tts_stream": "/v1/elevenlabs/text-to-speech/stream (ElevenLabs TTS streaming)",
            "elevenlabs_tts_ws": "/v1/elevenlabs/text-to-speech/websocket (ElevenLabs TTS WebSocket)",
            "elevenlabs_stt": "/v1/elevenlabs/speech-to-text (ElevenLabs speech-to-text)",
            "elevenlabs_stt_ws": "/v1/elevenlabs/speech-to-text/websocket (ElevenLabs STT WebSocket)",
            "serpapi_search": "/v1/serpapi/search (SerpAPI Google Search)",
            "serpapi_images": "/v1/serpapi/images (SerpAPI Google Images)",
            "serpapi_news": "/v1/serpapi/news (SerpAPI Google News)",
            "serpapi_shopping": "/v1/serpapi/shopping (SerpAPI Google Shopping)",
            "serpapi_maps": "/v1/serpapi/maps (SerpAPI Google Maps)",
            "tavily_search": "/v1/tavily/search (Tavily AI Search)",
            "tavily_extract": "/v1/tavily/extract (Tavily Content Extraction)",
            "health": "/health",
            "admin_ui": "/admin (Web-based admin interface)"
        }
    }


@app.get("/admin/login-page", response_class=HTMLResponse)
async def login_page():
    """Serve the login page."""
    try:
        with open("static/login.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Login page not found")


@app.get("/admin")
async def admin_ui(admin_session: Optional[str] = Cookie(None)):
    """Serve the admin UI. Redirects to login if not authenticated."""
    # Check if user has valid session
    if not admin_session or not admin_auth.admin_auth.verify_session(admin_session):
        # Redirect to login page
        return RedirectResponse(url="/admin/login-page", status_code=303)

    # User is authenticated, serve admin UI
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


@app.get("/v1/models")
async def list_models(user_info: Dict[str, Any] = Depends(get_current_user)):
    """
    List available models from all backend services.

    This endpoint queries all active backends and aggregates their models,
    grouped by backend. Requires authentication via Bearer token.
    """
    try:
        # Get all active backends
        backends = backend_manager.list_backends(active_only=True)

        if not backends:
            logger.warning("No active backends found")
            return {"object": "list", "data": [], "backends": []}

        all_models = []
        backends_info = []

        for backend in backends:
            try:
                # Extract base URL (remove /chat/completions or /messages if present)
                backend_url = backend['base_url']
                if '/chat/completions' in backend_url:
                    models_base_url = backend_url.replace('/chat/completions', '')
                elif '/messages' in backend_url:
                    models_base_url = backend_url.replace('/messages', '')
                else:
                    models_base_url = backend_url

                models_url = f"{models_base_url}/models"

                logger.info(f"Querying models from backend '{backend['short_name']}': {models_url}")

                # Query backend's models endpoint
                response = requests.get(
                    models_url,
                    headers={
                        "Authorization": f"Bearer {backend['api_key']}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    backend_models = response.json()
                    models_list = backend_models.get('data', [])

                    # Prefix model IDs with backend short_name
                    prefixed_models = []
                    for model in models_list:
                        prefixed_model = model.copy()
                        original_id = model.get('id', '')
                        prefixed_model['id'] = f"{backend['short_name']}/{original_id}"
                        prefixed_model['backend'] = backend['short_name']
                        prefixed_model['backend_name'] = backend['name']
                        prefixed_models.append(prefixed_model)

                    all_models.extend(prefixed_models)

                    backends_info.append({
                        "short_name": backend['short_name'],
                        "name": backend['name'],
                        "models_count": len(models_list),
                        "models": prefixed_models
                    })

                    logger.info(f"Retrieved {len(models_list)} models from backend '{backend['short_name']}'")
                else:
                    logger.error(f"Backend '{backend['short_name']}' returned error: {response.status_code}")

            except requests.exceptions.Timeout:
                logger.error(f"Timeout querying backend '{backend['short_name']}'")
            except Exception as e:
                logger.error(f"Error querying backend '{backend['short_name']}': {e}")

        logger.info(f"Successfully aggregated {len(all_models)} models from {len(backends_info)} backends")

        return {
            "object": "list",
            "data": all_models,
            "backends": backends_info
        }

    except Exception as e:
        logger.error(f"Error aggregating models from backends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/login")
async def admin_login(request: Request):
    """
    Admin login endpoint.

    Expects JSON body with username and password.
    Returns session token as cookie on success.
    """
    try:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Username and password are required"
            )

        # Verify credentials
        if not admin_auth.admin_auth.verify_credentials(username, password):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

        # Create session
        session_token = admin_auth.admin_auth.create_session(username)

        # Create response with session cookie
        response = JSONResponse(content={
            "success": True,
            "message": "Login successful"
        })

        # Set secure cookie (24 hour expiry)
        response.set_cookie(
            key="admin_session",
            value=session_token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="strict"
        )

        logger.info(f"Admin login successful: {username}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@app.post("/admin/logout")
async def admin_logout(admin_session: Optional[str] = Cookie(None)):
    """
    Admin logout endpoint.

    Deletes the session and clears the cookie.
    """
    if admin_session:
        admin_auth.admin_auth.delete_session(admin_session)
        logger.info("Admin logout successful")

    response = JSONResponse(content={
        "success": True,
        "message": "Logout successful"
    })

    # Clear the cookie
    response.delete_cookie(key="admin_session")
    return response


# ===== Backend Routing Helper =====

def resolve_backend_and_model(
    model_name: Optional[str],
    user_info: Dict[str, Any]
) -> tuple[Dict[str, Any], str, OpenAIClient]:
    """
    Determine which backend to use and the actual model name.

    Backend selection priority:
    1. If model has "backend/model" format → use specified backend
    2. If user API key has backend_id set → use that backend
    3. Otherwise → use default backend

    Args:
        model_name: Model name from request (may be None or "backend/model" format)
        user_info: User information from authentication

    Returns:
        Tuple of (backend_dict, resolved_model_name, openai_client)
    """
    backend = None
    resolved_model = model_name

    # Parse model name for "backend/model" format
    if model_name and '/' in model_name:
        parts = model_name.split('/', 1)
        backend_short_name = parts[0]
        resolved_model = parts[1] if len(parts) > 1 else None

        # Look up backend by short name
        backend = backend_manager.get_backend_by_short_name(backend_short_name)
        if not backend:
            raise HTTPException(
                status_code=400,
                detail=f"Backend '{backend_short_name}' not found or inactive"
            )

        logger.info(f"Using backend from model name: {backend_short_name} → {backend['name']}")

    # Check if user has a preferred backend configured
    elif user_info.get('api_key_id'):
        user_backend = backend_manager.get_user_backend(user_info['api_key_id'])
        if user_backend:
            backend = user_backend
            logger.info(f"Using user's preferred backend: {backend['short_name']} → {backend['name']}")

    # Fall back to default backend
    if not backend:
        backend = backend_manager.get_default_backend()
        if not backend:
            # If no backend configured, use the original global config
            logger.info("No backend services configured, using global config")
            return {
                'base_url': config.openai_base_url,
                'api_key': config.openai_api_key,
                'short_name': 'default',
                'default_model': config.openai_model
            }, resolved_model or config.openai_model, openai_client

        logger.info(f"Using default backend: {backend['short_name']} → {backend['name']}")

    # Use backend's default model if no model specified
    if not resolved_model:
        resolved_model = backend.get('default_model') or config.openai_model

    # Create OpenAIClient for this backend (or reuse global if same)
    if backend['base_url'] == config.openai_base_url and backend['api_key'] == config.openai_api_key:
        # Same as global config, reuse existing client
        client = openai_client
    else:
        # Different backend, create new client
        client = OpenAIClient(
            backend['base_url'],
            backend['api_key'],
            config.timeout
        )

    return backend, resolved_model, client


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
        original_had_model = 'model' in openai_request

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

        # Resolve backend and model
        # Priority: 1) Explicit model from request 2) Per-key model setting
        requested_model = openai_request.get('model') if original_had_model else user_info.get('model_name')
        backend, resolved_model, backend_client = resolve_backend_and_model(requested_model, user_info)

        # Update request with resolved model
        openai_request['model'] = resolved_model
        logger.info(f"Resolved backend: {backend.get('short_name', 'default')} | Model: {resolved_model}")

        # Store for fallback and usage tracking
        # Fallback model should be the backend's default model, not the user-specified one
        fallback_model = backend.get('default_model') or config.openai_model
        client_specified_model = original_had_model

        # Handle streaming vs non-streaming
        if is_streaming:
            logger.info("🔄 Passing through streaming request to backend...")

            async def stream_generator():
                """Generator for streaming responses."""
                nonlocal openai_request, fallback_model, client_specified_model, backend_client

                try:
                    async for line in backend_client.create_streaming_completion(openai_request):
                        yield f"{line}\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")

                    # Check if this is a model error and we can retry with fallback
                    is_model_error = False
                    error_str = str(e).lower()

                    # Check for model-related errors or generic 400 errors (likely model issues)
                    if 'model' in error_str and ('not found' in error_str or 'does not exist' in error_str or 'invalid' in error_str):
                        is_model_error = True
                    elif '400' in error_str or 'bad request' in error_str:
                        # 400 errors on streaming are often model-related
                        is_model_error = True
                    elif 'attempted to access streaming response content' in error_str:
                        # This specific error occurs with 400 status from httpx
                        is_model_error = True

                    if hasattr(e, 'response') and e.response:
                        try:
                            response_text = e.response.text if hasattr(e.response, 'text') else str(e.response)
                            response_lower = response_text.lower()
                            if 'model' in response_lower and ('not found' in response_lower or 'does not exist' in response_lower or 'no access' in response_lower or 'invalid' in response_lower):
                                is_model_error = True
                        except:
                            pass

                    # Retry with fallback model if it's a model error
                    if client_specified_model and is_model_error and openai_request.get('model') != fallback_model:
                        logger.warning(f"⚠️  Client-specified model '{openai_request.get('model')}' failed in streaming, falling back to: {fallback_model}")
                        openai_request['model'] = fallback_model
                        try:
                            async for line in backend_client.create_streaming_completion(openai_request):
                                yield f"{line}\n"
                            return
                        except Exception as retry_error:
                            logger.error(f"Fallback model also failed: {retry_error}")
                            error_line = f'data: {json.dumps({"error": f"Both specified and fallback models failed: {str(retry_error)}"})}\n\n'
                            yield error_line
                            return

                    error_line = f'data: {json.dumps({"error": str(e)})}\n\n'
                    yield error_line

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )

        # Non-streaming path
        logger.info(f"🔄 Passing through to backend: {backend.get('name', 'default')}...")
        try:
            openai_response = await backend_client.create_completion(openai_request)
            request_id = openai_response.get("id")
        except Exception as e:
            # Check if this is a model not found error and client specified a model
            is_model_error = False

            # Check exception message
            error_str = str(e).lower()
            if 'model' in error_str and ('not found' in error_str or 'does not exist' in error_str or 'invalid' in error_str):
                is_model_error = True

            # Also check response body if it's an HTTPStatusError
            if hasattr(e, 'response') and e.response:
                try:
                    response_body = e.response.text.lower()
                    if 'model' in response_body and ('not found' in response_body or 'does not exist' in response_body or 'no access' in response_body):
                        is_model_error = True
                except:
                    pass

            if client_specified_model and is_model_error:
                logger.warning(f"⚠️  Client-specified model '{openai_request.get('model')}' not found, falling back to: {fallback_model}")
                openai_request['model'] = fallback_model
                openai_response = await backend_client.create_completion(openai_request)
                request_id = openai_response.get("id")
            else:
                raise

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

        # Track usage with actual backend model used
        # Use model from response, or fall back to what we actually sent (not user input)
        backend_model = openai_response.get('model', openai_request.get('model'))
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/chat/completions',
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            model=backend_model,
            request_id=request_id,
            backend_url=backend.get('base_url', config.openai_base_url)
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

        # Check if client specified a model in the original request
        client_specified_model = 'model' in claude_request

        # Translate to OpenAI format
        openai_request = translator.translate_request_to_openai(claude_request)

        # Preserve streaming flag if requested
        if is_streaming_requested:
            openai_request['stream'] = True

        # Resolve backend and model
        # Priority: 1) Explicit model from request 2) Per-key model setting
        requested_model = claude_request.get('model') if client_specified_model else user_info.get('model_name')
        backend, resolved_model, backend_client = resolve_backend_and_model(requested_model, user_info)

        # Update request with resolved model
        openai_request['model'] = resolved_model
        logger.info(f"Resolved backend: {backend.get('short_name', 'default')} | Model: {resolved_model}")

        # Store for fallback and usage tracking
        # Fallback model should be the backend's default model, not the user-specified one
        fallback_model = backend.get('default_model') or config.openai_model

        logger.debug(f"Translated to OpenAI request: {json.dumps(openai_request, indent=2)}")

        # Handle streaming vs non-streaming
        if is_streaming_requested:
            logger.info(f"🔄 Processing streaming request via {backend.get('name', 'default')}...")

            async def stream_generator():
                """Generator for streaming responses."""
                nonlocal openai_request, fallback_model, client_specified_model, backend_client

                try:
                    async for line in backend_client.create_streaming_completion(openai_request):
                        # Pass through OpenAI format stream
                        # Note: For full Claude compatibility, would need to translate each chunk
                        yield f"{line}\n"
                except Exception as e:
                    logger.error(f"Streaming error: {e}")

                    # Check if this is a model error and we can retry with fallback
                    is_model_error = False
                    error_str = str(e).lower()

                    # Check for model-related errors or generic 400 errors (likely model issues)
                    if 'model' in error_str and ('not found' in error_str or 'does not exist' in error_str or 'invalid' in error_str):
                        is_model_error = True
                    elif '400' in error_str or 'bad request' in error_str:
                        # 400 errors on streaming are often model-related
                        is_model_error = True
                    elif 'attempted to access streaming response content' in error_str:
                        # This specific error occurs with 400 status from httpx
                        is_model_error = True

                    if hasattr(e, 'response') and e.response:
                        try:
                            response_text = e.response.text if hasattr(e.response, 'text') else str(e.response)
                            response_lower = response_text.lower()
                            if 'model' in response_lower and ('not found' in response_lower or 'does not exist' in response_lower or 'no access' in response_lower or 'invalid' in response_lower):
                                is_model_error = True
                        except:
                            pass

                    # Retry with fallback model if it's a model error
                    if client_specified_model and is_model_error and openai_request.get('model') != fallback_model:
                        logger.warning(f"⚠️  Client-specified model '{openai_request.get('model')}' failed in streaming, falling back to: {fallback_model}")
                        openai_request['model'] = fallback_model
                        try:
                            async for line in backend_client.create_streaming_completion(openai_request):
                                yield f"{line}\n"
                            return
                        except Exception as retry_error:
                            logger.error(f"Fallback model also failed: {retry_error}")
                            error_line = f'data: {json.dumps({"error": f"Both specified and fallback models failed: {str(retry_error)}"})}\n\n'
                            yield error_line
                            return

                    error_line = f'data: {json.dumps({"error": str(e)})}\n\n'
                    yield error_line

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )

        # Non-streaming path
        logger.info(f"🔄 Processing via backend: {backend.get('name', 'default')}...")
        try:
            openai_response = await backend_client.create_completion(openai_request)
            request_id = openai_response.get("id")
        except Exception as e:
            # Check if this is a model not found error and client specified a model
            is_model_error = False

            # Check exception message
            error_str = str(e).lower()
            if 'model' in error_str and ('not found' in error_str or 'does not exist' in error_str or 'invalid' in error_str):
                is_model_error = True

            # Also check response body if it's an HTTPStatusError
            if hasattr(e, 'response') and e.response:
                try:
                    response_body = e.response.text.lower()
                    if 'model' in response_body and ('not found' in response_body or 'does not exist' in response_body or 'no access' in response_body):
                        is_model_error = True
                except:
                    pass

            if client_specified_model and is_model_error:
                logger.warning(f"⚠️  Client-specified model '{openai_request.get('model')}' not found, falling back to: {fallback_model}")
                openai_request['model'] = fallback_model
                openai_response = await backend_client.create_completion(openai_request)
                request_id = openai_response.get("id")
            else:
                raise

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

        # Track usage with actual backend model used
        # Use model from response, or fall back to what we actually sent (not user input)
        backend_model = openai_response.get('model', openai_request.get('model'))
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/messages',
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=backend_model,
            request_id=request_id,
            backend_url=backend.get('base_url', config.openai_base_url)
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
async def create_user(
    username: str,
    email: Optional[str] = None,
    session: str = Depends(verify_admin_session)
):
    """
    Create a new user and automatically generate a default API key.

    Admin endpoint - requires authentication.

    Returns the user info and the generated API key (shown only once).
    """
    try:
        # Create the user
        user_id = user_manager.create_user(username, email)

        # Automatically create a default API key
        api_key = user_manager.create_api_key(user_id, name="Default Key")

        # Send email with API key if email address is provided
        email_sent = False
        if email and email_sender:
            email_sent = email_sender.send_api_key_email(username, email, api_key)
            if email_sent:
                logger.info(f"✅ API key email sent to {email}")
            else:
                logger.warning(f"⚠️ Failed to send API key email to {email}")

        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "api_key": api_key,
            "email_sent": email_sent,
            "message": f"User {username} created successfully",
            "warning": "Save this API key! It will not be shown again."
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin/users/batch")
async def create_users_batch(
    csv_file: Optional[UploadFile] = File(None),
    csv_text: Optional[str] = Form(None),
    session: str = Depends(verify_admin_session)
):
    """
    Batch create users from CSV file or text input.

    Admin endpoint - requires authentication.

    Accepts either:
    - csv_file: Uploaded CSV file
    - csv_text: CSV content as text

    CSV format: username,email (no header required)

    Returns CSV with: username,email,api_key
    - If creation succeeds: actual API key
    - If creation fails: "user_creation_failed"
    """
    try:
        # Get CSV content from either file upload or text input
        if csv_file:
            content = await csv_file.read()
            csv_content = content.decode('utf-8')
        elif csv_text:
            csv_content = csv_text
        else:
            raise HTTPException(
                status_code=400,
                detail="Either csv_file or csv_text must be provided"
            )

        # Parse CSV input
        csv_reader = csv.reader(io.StringIO(csv_content))
        results = []

        for row in csv_reader:
            # Skip empty rows
            if not row or len(row) == 0:
                continue

            # Extract username and email
            username = row[0].strip() if len(row) > 0 else ""
            email = row[1].strip() if len(row) > 1 else ""

            if not username:
                # Skip rows without username
                continue

            # Try to create user and generate API key
            try:
                user_id = user_manager.create_user(username, email if email else None)
                api_key = user_manager.create_api_key(user_id, name="Default Key")

                # Send email with API key if email address is provided
                email_sent = False
                if email and email_sender:
                    email_sent = email_sender.send_api_key_email(username, email, api_key)
                    if email_sent:
                        logger.info(f"✅ API key email sent to {email} for user {username}")

                results.append({
                    "username": username,
                    "email": email,
                    "api_key": api_key,
                    "email_sent": email_sent
                })
                logger.info(f"Batch created user: {username}")

            except Exception as e:
                logger.error(f"Failed to create user {username}: {e}")
                results.append({
                    "username": username,
                    "email": email,
                    "api_key": "user_creation_failed"
                })

        # Generate CSV output
        output = io.StringIO()
        csv_writer = csv.writer(output)
        csv_writer.writerow(["username", "email", "api_key"])

        for result in results:
            csv_writer.writerow([
                result["username"],
                result["email"],
                result["api_key"]
            ])

        # Return as CSV file download
        csv_output = output.getvalue()
        return StreamingResponse(
            io.BytesIO(csv_output.encode('utf-8')),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=users_with_keys.csv"
            }
        )

    except Exception as e:
        logger.error(f"Batch user creation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch creation failed: {str(e)}")


@app.post("/admin/api-keys")
async def create_api_key_endpoint(
    user_id: int,
    name: Optional[str] = None,
    session: str = Depends(verify_admin_session)
):
    """
    Create a new API key for a user.

    Admin endpoint - requires authentication.

    Returns the API key - this is the ONLY time it will be shown!
    """
    try:
        api_key = user_manager.create_api_key(user_id, name)

        # Get user info to send email
        users = user_manager.list_users()
        user = next((u for u in users if u['id'] == user_id), None)

        # Send email with API key if user has email
        email_sent = False
        if user and user.get('email') and email_sender:
            email_sent = email_sender.send_api_key_email(
                user['username'],
                user['email'],
                api_key
            )
            if email_sent:
                logger.info(f"✅ API key email sent to {user['email']}")
            else:
                logger.warning(f"⚠️ Failed to send API key email to {user['email']}")

        return {
            "success": True,
            "api_key": api_key,
            "user_id": user_id,
            "name": name,
            "email_sent": email_sent,
            "warning": "Save this API key! It will not be shown again."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/admin/send-api-key-email")
async def send_api_key_email_endpoint(
    user_id: int,
    api_key: str,
    email: Optional[str] = None,
    session: str = Depends(verify_admin_session)
):
    """
    Manually send an API key to a user's email.

    Admin endpoint - requires authentication.

    Parameters:
    - user_id: The user's ID
    - api_key: The plain text API key to send
    - email: Optional email override (if not provided, uses user's registered email)

    This is useful for:
    - Resending emails when automatic sending failed
    - Sending to a different email address
    """
    try:
        # Get user info
        users = user_manager.list_users()
        user = next((u for u in users if u['id'] == user_id), None)

        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Use provided email or user's registered email
        target_email = email if email else user.get('email')

        if not target_email:
            raise HTTPException(
                status_code=400,
                detail="No email address provided and user has no registered email"
            )

        # Send email
        if not email_sender:
            raise HTTPException(status_code=500, detail="Email service not available")

        email_sent = email_sender.send_api_key_email(
            user['username'],
            target_email,
            api_key
        )

        if email_sent:
            logger.info(f"✅ Manually sent API key email to {target_email}")
            return {
                "success": True,
                "message": f"API key email sent to {target_email}",
                "email": target_email
            }
        else:
            logger.error(f"❌ Failed to send API key email to {target_email}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send email to {target_email}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending API key email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/users/{user_id}/generate-and-send-key")
async def generate_and_send_key_endpoint(
    user_id: int,
    session: str = Depends(verify_admin_session)
):
    """
    Generate a new API key for a user and automatically send it via email.

    Admin endpoint - requires authentication.

    Parameters:
    - user_id: The user's ID

    Returns the new API key (shown only once) and email status.
    """
    try:
        # Get user info
        users = user_manager.list_users()
        user = next((u for u in users if u['id'] == user_id), None)

        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        if not user.get('email'):
            raise HTTPException(
                status_code=400,
                detail=f"User {user['username']} has no email address"
            )

        # Generate new API key
        api_key = user_manager.create_api_key(user_id, name="Admin Generated Key")

        # Send email
        email_sent = False
        if email_sender:
            email_sent = email_sender.send_api_key_email(
                user['username'],
                user['email'],
                api_key
            )
            if email_sent:
                logger.info(f"✅ Generated and sent API key to {user['email']}")
            else:
                logger.warning(f"⚠️ Generated key but failed to send email to {user['email']}")

        return {
            "success": True,
            "api_key": api_key,
            "email_sent": email_sent,
            "email": user['email'],
            "username": user['username'],
            "message": f"New API key generated and {'sent to' if email_sent else 'could not be sent to'} {user['email']}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating and sending API key for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/users")
async def list_users_endpoint(session: str = Depends(verify_admin_session)):
    """
    List all users.

    Admin endpoint - requires authentication.
    """
    users = user_manager.list_users()
    return {"users": users}


@app.get("/admin/api-keys")
async def list_api_keys_endpoint(
    user_id: Optional[int] = None,
    session: str = Depends(verify_admin_session)
):
    """
    List API keys, optionally filtered by user.

    Admin endpoint - requires authentication.
    """
    api_keys = user_manager.list_api_keys(user_id)
    return {"api_keys": api_keys}


@app.delete("/admin/api-keys/{api_key_id}")
async def deactivate_api_key_endpoint(
    api_key_id: int,
    session: str = Depends(verify_admin_session)
):
    """
    Deactivate an API key.

    Admin endpoint - requires authentication.
    """
    try:
        user_manager.deactivate_api_key(api_key_id)
        return {
            "success": True,
            "message": f"API key {api_key_id} deactivated"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/admin/users/{user_id}")
async def delete_user_endpoint(
    user_id: int,
    session: str = Depends(verify_admin_session)
):
    """
    Delete a user and all associated API keys and usage records.

    Admin endpoint - requires authentication.

    WARNING: This is a destructive operation that cannot be undone.
    Deletes:
    - The user account
    - All API keys for this user
    - All usage records for those API keys
    """
    try:
        user_manager.delete_user(user_id)
        return {
            "success": True,
            "message": f"User {user_id} and all associated data deleted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


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


@app.get("/admin/usage/by-backend")
async def get_usage_by_backend_endpoint():
    """
    Get usage statistics grouped by backend URL and model.

    Admin endpoint - shows which backend models are actually being used.
    """
    usage = user_manager.get_all_usage_by_backend()
    return usage


@app.get("/usage/api-key/{key_id}/by-backend")
async def get_api_key_usage_by_backend_endpoint(key_id: int):
    """
    Get usage statistics for a specific API key grouped by backend URL and model.

    Shows which backend models are being used by this specific API key.
    """
    usage = user_manager.get_api_key_usage_by_backend(key_id)
    return usage


@app.get("/admin/users/{user_id}/usage/by-backend")
async def get_user_usage_by_backend_endpoint(user_id: int):
    """
    Get usage statistics for a specific user grouped by backend URL and model.

    Admin endpoint - shows which backend models are being used by this user across all their API keys.
    """
    usage = user_manager.get_user_usage_by_backend(user_id)
    return usage


# ===== Backend Management Admin Endpoints =====

@app.get("/admin/backends")
async def list_backends_endpoint(
    active_only: bool = False,
    session: str = Depends(verify_admin_session)
):
    """
    List all backend services.

    Query params:
        active_only: If true, only return active backends

    Admin endpoint - requires authentication.
    """
    backends = backend_manager.list_backends(active_only=active_only)
    return backends


@app.post("/admin/backends")
async def create_backend_endpoint(
    request: Request,
    session: str = Depends(verify_admin_session)
):
    """
    Create a new backend service.

    Body:
        short_name: Short identifier (e.g., "inf", "zhipu", "sf")
        name: Display name
        base_url: API base URL
        api_key: API key for the backend
        default_model: Default model for this backend (optional)
        is_default: Whether this is the default backend (optional)
    """
    data = await request.json()

    try:
        backend_id = backend_manager.create_backend(
            short_name=data['short_name'],
            name=data['name'],
            base_url=data['base_url'],
            api_key=data['api_key'],
            default_model=data.get('default_model'),
            is_default=data.get('is_default', False)
        )

        return {
            "success": True,
            "backend_id": backend_id,
            "message": f"Backend '{data['short_name']}' created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")


@app.get("/admin/backends/{backend_id}")
async def get_backend_endpoint(
    backend_id: int,
    session: str = Depends(verify_admin_session)
):
    """Get details of a specific backend service."""
    backend = backend_manager.get_backend(backend_id)

    if not backend:
        raise HTTPException(status_code=404, detail=f"Backend {backend_id} not found")

    return backend


@app.put("/admin/backends/{backend_id}")
async def update_backend_endpoint(
    backend_id: int,
    request: Request,
    session: str = Depends(verify_admin_session)
):
    """
    Update a backend service.

    Body (all fields optional):
        short_name: Short identifier
        name: Display name
        base_url: API base URL
        api_key: API key
        default_model: Default model
        is_active: Active status
        is_default: Default backend status
    """
    data = await request.json()

    try:
        success = backend_manager.update_backend(
            backend_id=backend_id,
            short_name=data.get('short_name'),
            name=data.get('name'),
            base_url=data.get('base_url'),
            api_key=data.get('api_key'),
            default_model=data.get('default_model'),
            is_active=data.get('is_active'),
            is_default=data.get('is_default')
        )

        if not success:
            raise HTTPException(status_code=404, detail=f"Backend {backend_id} not found")

        return {
            "success": True,
            "message": f"Backend {backend_id} updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/admin/backends/{backend_id}")
async def delete_backend_endpoint(
    backend_id: int,
    session: str = Depends(verify_admin_session)
):
    """
    Delete a backend service.

    WARNING: This will fail if any API keys are using this backend.
    Consider setting is_active=False instead.
    """
    try:
        success = backend_manager.delete_backend(backend_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Backend {backend_id} not found")

        return {
            "success": True,
            "message": f"Backend {backend_id} deleted successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/admin/backends/{backend_id}/models")
async def list_backend_models_endpoint(
    backend_id: int,
    session: str = Depends(verify_admin_session)
):
    """
    List available models from a specific backend service.

    This makes a request to the backend's /v1/models endpoint.

    Admin endpoint - requires authentication.
    """
    backend = backend_manager.get_backend(backend_id)

    if not backend:
        raise HTTPException(status_code=404, detail=f"Backend {backend_id} not found")

    try:
        # Construct models URL
        base_url = backend['base_url']
        if '/chat/completions' in base_url:
            models_url = base_url.replace('/chat/completions', '/models')
        elif '/messages' in base_url:
            models_url = base_url.replace('/messages', '/models')
        else:
            models_url = f"{base_url}/models"

        # Make request to backend
        headers = {
            "Authorization": f"Bearer {backend['api_key']}",
            "Content-Type": "application/json"
        }

        response = requests.get(models_url, headers=headers, timeout=10)
        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:
        logger.error(f"Failed to fetch models from backend {backend_id}: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch models from backend: {str(e)}"
        )


@app.get("/settings/model")
async def get_model_setting(user_info: Dict[str, Any] = Depends(get_current_user)):
    """
    Get the model name setting for the authenticated user's API key.

    Returns the custom model name if set, or null if using the global default.

    Requires authentication via Bearer token.
    """
    model_name = user_manager.get_model_setting(user_info['api_key_id'])
    return {
        "api_key_id": user_info['api_key_id'],
        "api_key_name": user_info.get('api_key_name'),
        "model_name": model_name,
        "using_default": model_name is None
    }


@app.put("/settings/model")
async def set_model_setting(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Set the model name for the authenticated user's API key.

    Request body:
    {
        "model_name": "gpt-4" or null to use global default
    }

    Requires authentication via Bearer token.
    """
    try:
        body = await request.json()
        model_name = body.get("model_name")

        # Validate model_name is either a string or None
        if model_name is not None and not isinstance(model_name, str):
            raise HTTPException(
                status_code=400,
                detail="model_name must be a string or null"
            )

        # Set the model for this API key
        user_manager.set_model_setting(user_info['api_key_id'], model_name)

        logger.info(
            f"User {user_info['username']} set model to {model_name} "
            f"for API key {user_info['api_key_id']}"
        )

        return {
            "success": True,
            "api_key_id": user_info['api_key_id'],
            "model_name": model_name,
            "message": f"Model set to {model_name}" if model_name else "Using global default model"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set model: {str(e)}")


# ===== Firecrawl Proxy Endpoints =====

@app.post("/v1/firecrawl/scrape")
async def firecrawl_scrape(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Firecrawl scrape endpoint - proxy to Firecrawl API.

    Scrapes a single URL and returns the content.

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get Firecrawl configuration from environment
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        firecrawl_base_url = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v1")

        if not firecrawl_api_key:
            raise HTTPException(
                status_code=503,
                detail="Firecrawl API key not configured"
            )

        # Parse request body
        body = await request.json()
        url = body.get("url")

        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        logger.info("=" * 80)
        logger.info(f"📥 FIRECRAWL SCRAPE REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"URL: {url}")
        logger.info(f"Options: {body.get('formats', ['markdown'])}")

        # Forward request to Firecrawl API
        firecrawl_url = f"{firecrawl_base_url}/scrape"
        headers = {
            "Authorization": f"Bearer {firecrawl_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            firecrawl_url,
            headers=headers,
            json=body,
            timeout=config.timeout
        )

        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ FIRECRAWL SCRAPE COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Status: {result.get('success', False)}")
        logger.info("=" * 80)

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/firecrawl/scrape',
            input_tokens=0,
            output_tokens=0,
            model='firecrawl-scrape',
            request_id=None,
            backend_url=firecrawl_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ FIRECRAWL API ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.error("=" * 80)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/v1/firecrawl/crawl")
async def firecrawl_crawl(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Firecrawl crawl endpoint - proxy to Firecrawl API.

    Starts a crawl job for a website.

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get Firecrawl configuration from environment
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        firecrawl_base_url = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v1")

        if not firecrawl_api_key:
            raise HTTPException(
                status_code=503,
                detail="Firecrawl API key not configured"
            )

        # Parse request body
        body = await request.json()
        url = body.get("url")

        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        logger.info("=" * 80)
        logger.info(f"📥 FIRECRAWL CRAWL REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"URL: {url}")
        logger.info(f"Max depth: {body.get('limit', 100)}")

        # Forward request to Firecrawl API
        firecrawl_url = f"{firecrawl_base_url}/crawl"
        headers = {
            "Authorization": f"Bearer {firecrawl_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            firecrawl_url,
            headers=headers,
            json=body,
            timeout=config.timeout
        )

        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ FIRECRAWL CRAWL STARTED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Job ID: {result.get('id', 'N/A')}")
        logger.info("=" * 80)

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/firecrawl/crawl',
            input_tokens=0,
            output_tokens=0,
            model='firecrawl-crawl',
            request_id=result.get('id'),
            backend_url=firecrawl_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ FIRECRAWL API ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.error("=" * 80)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/v1/firecrawl/crawl/status/{job_id}")
async def firecrawl_crawl_status(
    job_id: str,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Firecrawl crawl status endpoint - proxy to Firecrawl API.

    Check the status of a crawl job.

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get Firecrawl configuration from environment
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        firecrawl_base_url = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v1")

        if not firecrawl_api_key:
            raise HTTPException(
                status_code=503,
                detail="Firecrawl API key not configured"
            )

        logger.info("=" * 80)
        logger.info(f"📥 FIRECRAWL STATUS REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Job ID: {job_id}")

        # Forward request to Firecrawl API
        firecrawl_url = f"{firecrawl_base_url}/crawl/status/{job_id}"
        headers = {
            "Authorization": f"Bearer {firecrawl_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.get(
            firecrawl_url,
            headers=headers,
            timeout=config.timeout
        )

        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ FIRECRAWL STATUS RETRIEVED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Status: {result.get('status', 'unknown')}")
        logger.info("=" * 80)

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ FIRECRAWL API ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.error("=" * 80)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/v1/firecrawl/search")
async def firecrawl_search(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Firecrawl search endpoint - proxy to Firecrawl API.

    Search the web and return results.

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get Firecrawl configuration from environment
        firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
        firecrawl_base_url = os.getenv("FIRECRAWL_BASE_URL", "https://api.firecrawl.dev/v1")

        if not firecrawl_api_key:
            raise HTTPException(
                status_code=503,
                detail="Firecrawl API key not configured"
            )

        # Parse request body
        body = await request.json()
        query = body.get("query")

        if not query:
            raise HTTPException(status_code=400, detail="Query is required")

        logger.info("=" * 80)
        logger.info(f"📥 FIRECRAWL SEARCH REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Query: {query}")
        logger.info(f"Limit: {body.get('limit', 10)}")

        # Forward request to Firecrawl API
        firecrawl_url = f"{firecrawl_base_url}/search"
        headers = {
            "Authorization": f"Bearer {firecrawl_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            firecrawl_url,
            headers=headers,
            json=body,
            timeout=config.timeout
        )

        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ FIRECRAWL SEARCH COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Results: {len(result.get('data', []))}")
        logger.info("=" * 80)

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/firecrawl/search',
            input_tokens=0,
            output_tokens=0,
            model='firecrawl-search',
            request_id=None,
            backend_url=firecrawl_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ FIRECRAWL API ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.error("=" * 80)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ===== ElevenLabs Proxy Endpoints =====

@app.post("/v1/elevenlabs/text-to-speech")
async def elevenlabs_text_to_speech(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    ElevenLabs text-to-speech endpoint - proxy to ElevenLabs API.

    Converts text to speech using specified voice.

    Request body:
    {
        "text": "Text to convert to speech",
        "voice_id": "voice_id or use default",
        "model_id": "eleven_monolingual_v1 (optional)",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get ElevenLabs configuration from environment
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        elevenlabs_base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")

        if not elevenlabs_api_key:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs API key not configured"
            )

        # Parse request body
        body = await request.json()
        text = body.get("text")
        voice_id = body.get("voice_id", "21m00Tcm4TlvDq8ikWAM")  # Default voice

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        logger.info("=" * 80)
        logger.info(f"📥 ELEVENLABS TEXT-TO-SPEECH REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Voice ID: {voice_id}")
        logger.info(f"Text length: {len(text)} characters")
        logger.info(f"Model: {body.get('model_id', 'default')}")

        # Prepare request to ElevenLabs API
        elevenlabs_url = f"{elevenlabs_base_url}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        }

        # Build request body
        tts_body = {
            "text": text,
            "model_id": body.get("model_id", "eleven_monolingual_v1")
        }

        if "voice_settings" in body:
            tts_body["voice_settings"] = body["voice_settings"]

        # Make request to ElevenLabs API
        response = requests.post(
            elevenlabs_url,
            headers=headers,
            json=tts_body,
            timeout=config.timeout
        )

        response.raise_for_status()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ ELEVENLABS TTS COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Audio size: {len(response.content)} bytes")
        logger.info("=" * 80)

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/elevenlabs/text-to-speech',
            input_tokens=len(text),
            output_tokens=0,
            model='elevenlabs-tts',
            request_id=None,
            backend_url=elevenlabs_base_url
        )

        # Return audio data
        return Response(
            content=response.content,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech_{int(time.time())}.mp3"
            }
        )

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ ELEVENLABS API ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.error("=" * 80)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/v1/elevenlabs/text-to-speech/stream")
async def elevenlabs_text_to_speech_stream(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    ElevenLabs text-to-speech streaming endpoint - proxy to ElevenLabs API.

    Converts text to speech with streaming response.

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get ElevenLabs configuration from environment
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        elevenlabs_base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")

        if not elevenlabs_api_key:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs API key not configured"
            )

        # Parse request body
        body = await request.json()
        text = body.get("text")
        voice_id = body.get("voice_id", "21m00Tcm4TlvDq8ikWAM")

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        logger.info("=" * 80)
        logger.info(f"📥 ELEVENLABS TTS STREAMING REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Voice ID: {voice_id}")
        logger.info(f"Text length: {len(text)} characters")

        # Prepare request to ElevenLabs API
        elevenlabs_url = f"{elevenlabs_base_url}/text-to-speech/{voice_id}/stream"
        headers = {
            "xi-api-key": elevenlabs_api_key,
            "Content-Type": "application/json"
        }

        tts_body = {
            "text": text,
            "model_id": body.get("model_id", "eleven_monolingual_v1")
        }

        if "voice_settings" in body:
            tts_body["voice_settings"] = body["voice_settings"]

        # Stream response
        async def audio_stream():
            """Generator for streaming audio."""
            try:
                with requests.post(
                    elevenlabs_url,
                    headers=headers,
                    json=tts_body,
                    stream=True,
                    timeout=config.timeout
                ) as response:
                    response.raise_for_status()

                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk

                elapsed_time = time.time() - start_time
                logger.info(f"✅ ELEVENLABS TTS STREAMING COMPLETED")
                logger.info(f"Duration: {elapsed_time:.2f}s")
                logger.info("=" * 80)

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                raise

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/elevenlabs/text-to-speech/stream',
            input_tokens=len(text),
            output_tokens=0,
            model='elevenlabs-tts-stream',
            request_id=None,
            backend_url=elevenlabs_base_url
        )

        return StreamingResponse(
            audio_stream(),
            media_type="audio/mpeg",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.websocket("/v1/elevenlabs/text-to-speech/websocket")
async def elevenlabs_text_to_speech_websocket(
    websocket: WebSocket,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    api_key: Optional[str] = None
):
    """
    ElevenLabs text-to-speech WebSocket endpoint.

    Real-time text-to-speech streaming via WebSocket.

    Query parameters:
    - voice_id: Voice ID (default: 21m00Tcm4TlvDq8ikWAM)
    - api_key: User API key for authentication

    WebSocket message format (send):
    {
        "text": "Text to convert",
        "voice_settings": {...} (optional)
    }

    WebSocket message format (receive):
    Binary audio data chunks
    """
    await websocket.accept()

    try:
        # Validate API key
        if not api_key:
            await websocket.send_json({"error": "API key required"})
            await websocket.close()
            return

        user_info = user_manager.validate_api_key(api_key)
        if not user_info:
            await websocket.send_json({"error": "Invalid API key"})
            await websocket.close()
            return

        # Get ElevenLabs configuration
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        elevenlabs_ws_url = os.getenv("ELEVENLABS_WS_URL", "wss://api.elevenlabs.io/v1")

        if not elevenlabs_api_key:
            await websocket.send_json({"error": "ElevenLabs API not configured"})
            await websocket.close()
            return

        logger.info(f"📥 ELEVENLABS TTS WebSocket connected for user: {user_info['username']}")

        # Connect to ElevenLabs WebSocket
        elevenlabs_ws_endpoint = f"{elevenlabs_ws_url}/text-to-speech/{voice_id}/stream-input?model_id=eleven_monolingual_v1"

        async with websockets.connect(
            elevenlabs_ws_endpoint,
            extra_headers={"xi-api-key": elevenlabs_api_key}
        ) as elevenlabs_ws:

            # Handle bidirectional communication
            async def receive_from_client():
                """Receive text from client and forward to ElevenLabs"""
                try:
                    while True:
                        data = await websocket.receive_text()
                        message = json.loads(data)

                        # Forward to ElevenLabs
                        await elevenlabs_ws.send(json.dumps(message))

                        # Track usage
                        text = message.get("text", "")
                        user_manager.track_usage(
                            api_key_id=user_info['api_key_id'],
                            endpoint='/v1/elevenlabs/text-to-speech/websocket',
                            input_tokens=len(text),
                            output_tokens=0,
                            model='elevenlabs-tts-ws',
                            request_id=None,
                            backend_url=elevenlabs_ws_url
                        )

                except WebSocketDisconnect:
                    logger.info(f"Client disconnected: {user_info['username']}")
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")

            async def send_to_client():
                """Receive audio from ElevenLabs and forward to client"""
                try:
                    async for message in elevenlabs_ws:
                        if isinstance(message, bytes):
                            # Audio data
                            await websocket.send_bytes(message)
                        else:
                            # JSON message
                            await websocket.send_text(message)

                except Exception as e:
                    logger.error(f"Error sending to client: {e}")

            # Run both directions concurrently
            await asyncio.gather(
                receive_from_client(),
                send_to_client()
            )

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("WebSocket connection closed")


@app.post("/v1/elevenlabs/speech-to-text")
async def elevenlabs_speech_to_text(
    audio_file: UploadFile = File(...),
    model: Optional[str] = Form("whisper-1"),
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    ElevenLabs speech-to-text endpoint - proxy to ElevenLabs API.

    Transcribes audio to text.

    Form data:
    - audio_file: Audio file to transcribe
    - model: Model to use (default: whisper-1)

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get ElevenLabs configuration from environment
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        elevenlabs_base_url = os.getenv("ELEVENLABS_BASE_URL", "https://api.elevenlabs.io/v1")

        if not elevenlabs_api_key:
            raise HTTPException(
                status_code=503,
                detail="ElevenLabs API key not configured"
            )

        logger.info("=" * 80)
        logger.info(f"📥 ELEVENLABS SPEECH-TO-TEXT REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"File: {audio_file.filename}")
        logger.info(f"Model: {model}")

        # Read audio file
        audio_data = await audio_file.read()

        # Prepare request to ElevenLabs API
        elevenlabs_url = f"{elevenlabs_base_url}/speech-to-text"
        headers = {
            "xi-api-key": elevenlabs_api_key
        }

        # Send as multipart/form-data
        files = {
            'file': (audio_file.filename, audio_data, audio_file.content_type)
        }
        data = {
            'model_id': model
        }

        response = requests.post(
            elevenlabs_url,
            headers=headers,
            files=files,
            data=data,
            timeout=config.timeout
        )

        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ ELEVENLABS STT COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Transcription length: {len(result.get('text', ''))} characters")
        logger.info("=" * 80)

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/elevenlabs/speech-to-text',
            input_tokens=0,
            output_tokens=len(result.get('text', '')),
            model='elevenlabs-stt',
            request_id=None,
            backend_url=elevenlabs_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ ELEVENLABS API ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.error("=" * 80)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.websocket("/v1/elevenlabs/speech-to-text/websocket")
async def elevenlabs_speech_to_text_websocket(
    websocket: WebSocket,
    api_key: Optional[str] = None,
    model: str = "whisper-1"
):
    """
    ElevenLabs speech-to-text WebSocket endpoint.

    Real-time speech-to-text transcription via WebSocket.

    Query parameters:
    - api_key: User API key for authentication
    - model: Model to use (default: whisper-1)

    WebSocket message format (send):
    Binary audio data chunks

    WebSocket message format (receive):
    {
        "text": "Transcribed text",
        "is_final": true/false
    }
    """
    await websocket.accept()

    try:
        # Validate API key
        if not api_key:
            await websocket.send_json({"error": "API key required"})
            await websocket.close()
            return

        user_info = user_manager.validate_api_key(api_key)
        if not user_info:
            await websocket.send_json({"error": "Invalid API key"})
            await websocket.close()
            return

        # Get ElevenLabs configuration
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        elevenlabs_ws_url = os.getenv("ELEVENLABS_WS_URL", "wss://api.elevenlabs.io/v1")

        if not elevenlabs_api_key:
            await websocket.send_json({"error": "ElevenLabs API not configured"})
            await websocket.close()
            return

        logger.info(f"📥 ELEVENLABS STT WebSocket connected for user: {user_info['username']}")

        # Connect to ElevenLabs WebSocket
        elevenlabs_ws_endpoint = f"{elevenlabs_ws_url}/speech-to-text/stream?model={model}"

        async with websockets.connect(
            elevenlabs_ws_endpoint,
            extra_headers={"xi-api-key": elevenlabs_api_key}
        ) as elevenlabs_ws:

            # Handle bidirectional communication
            async def receive_from_client():
                """Receive audio from client and forward to ElevenLabs"""
                try:
                    while True:
                        data = await websocket.receive_bytes()

                        # Forward audio to ElevenLabs
                        await elevenlabs_ws.send(data)

                except WebSocketDisconnect:
                    logger.info(f"Client disconnected: {user_info['username']}")
                except Exception as e:
                    logger.error(f"Error receiving from client: {e}")

            async def send_to_client():
                """Receive transcriptions from ElevenLabs and forward to client"""
                try:
                    async for message in elevenlabs_ws:
                        # Forward transcription to client
                        await websocket.send_text(message)

                        # Track usage
                        try:
                            result = json.loads(message)
                            text = result.get("text", "")
                            if result.get("is_final", False):
                                user_manager.track_usage(
                                    api_key_id=user_info['api_key_id'],
                                    endpoint='/v1/elevenlabs/speech-to-text/websocket',
                                    input_tokens=0,
                                    output_tokens=len(text),
                                    model='elevenlabs-stt-ws',
                                    request_id=None,
                                    backend_url=elevenlabs_ws_url
                                )
                        except:
                            pass

                except Exception as e:
                    logger.error(f"Error sending to client: {e}")

            # Run both directions concurrently
            await asyncio.gather(
                receive_from_client(),
                send_to_client()
            )

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("WebSocket connection closed")


# ===== SerpAPI Proxy Endpoints =====

@app.get("/v1/serpapi/search")
async def serpapi_search(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    SerpAPI Google Search endpoint - proxy to SerpAPI.

    Performs Google search and returns structured results.

    Query parameters:
    - q: Search query (required)
    - location: Location for search (optional)
    - gl: Country code (optional, e.g., "us", "uk")
    - hl: Language code (optional, e.g., "en", "es")
    - num: Number of results (optional, default: 10)
    - start: Pagination start (optional)

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        # Get SerpAPI configuration from environment
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com")

        if not serpapi_api_key:
            raise HTTPException(
                status_code=503,
                detail="SerpAPI key not configured"
            )

        # Get query parameters
        query_params = dict(request.query_params)
        query = query_params.get("q")

        if not query:
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

        logger.info("=" * 80)
        logger.info(f"📥 SERPAPI GOOGLE SEARCH REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Query: {query}")
        logger.info(f"Parameters: {query_params}")

        # Prepare request to SerpAPI
        serpapi_url = f"{serpapi_base_url}/search"
        params = {
            "api_key": serpapi_api_key,
            "engine": "google",
            **query_params
        }

        response = requests.get(
            serpapi_url,
            params=params,
            timeout=config.timeout
        )

        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ SERPAPI SEARCH COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Results: {len(result.get('organic_results', []))}")
        logger.info("=" * 80)

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/serpapi/search',
            input_tokens=len(query),
            output_tokens=len(str(result)),
            model='serpapi-google-search',
            request_id=None,
            backend_url=serpapi_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ SERPAPI API ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {e}")
        if e.response is not None:
            logger.error(f"Response: {e.response.text}")
        logger.error("=" * 80)
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error("=" * 80)
        logger.error(f"❌ INTERNAL ERROR")
        logger.error(f"Duration: {elapsed_time:.2f}s")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/v1/serpapi/images")
async def serpapi_images(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    SerpAPI Google Images endpoint - proxy to SerpAPI.

    Searches Google Images and returns structured results.

    Query parameters:
    - q: Search query (required)
    - location: Location for search (optional)
    - gl: Country code (optional)
    - hl: Language code (optional)
    - num: Number of results (optional)

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com")

        if not serpapi_api_key:
            raise HTTPException(status_code=503, detail="SerpAPI key not configured")

        query_params = dict(request.query_params)
        query = query_params.get("q")

        if not query:
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

        logger.info("=" * 80)
        logger.info(f"📥 SERPAPI GOOGLE IMAGES REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Query: {query}")

        serpapi_url = f"{serpapi_base_url}/search"
        params = {
            "api_key": serpapi_api_key,
            "engine": "google",
            "tbm": "isch",  # Google Images
            **query_params
        }

        response = requests.get(serpapi_url, params=params, timeout=config.timeout)
        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ SERPAPI IMAGES COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Images: {len(result.get('images_results', []))}")
        logger.info("=" * 80)

        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/serpapi/images',
            input_tokens=len(query),
            output_tokens=len(str(result)),
            model='serpapi-google-images',
            request_id=None,
            backend_url=serpapi_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ SERPAPI IMAGES ERROR: {e}")
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ INTERNAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/v1/serpapi/news")
async def serpapi_news(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    SerpAPI Google News endpoint - proxy to SerpAPI.

    Searches Google News and returns structured results.

    Query parameters:
    - q: Search query (required)
    - location: Location for search (optional)
    - gl: Country code (optional)
    - hl: Language code (optional)
    - num: Number of results (optional)

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com")

        if not serpapi_api_key:
            raise HTTPException(status_code=503, detail="SerpAPI key not configured")

        query_params = dict(request.query_params)
        query = query_params.get("q")

        if not query:
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

        logger.info("=" * 80)
        logger.info(f"📥 SERPAPI GOOGLE NEWS REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Query: {query}")

        serpapi_url = f"{serpapi_base_url}/search"
        params = {
            "api_key": serpapi_api_key,
            "engine": "google",
            "tbm": "nws",  # Google News
            **query_params
        }

        response = requests.get(serpapi_url, params=params, timeout=config.timeout)
        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ SERPAPI NEWS COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"News articles: {len(result.get('news_results', []))}")
        logger.info("=" * 80)

        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/serpapi/news',
            input_tokens=len(query),
            output_tokens=len(str(result)),
            model='serpapi-google-news',
            request_id=None,
            backend_url=serpapi_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ SERPAPI NEWS ERROR: {e}")
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ INTERNAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/v1/serpapi/shopping")
async def serpapi_shopping(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    SerpAPI Google Shopping endpoint - proxy to SerpAPI.

    Searches Google Shopping and returns product results.

    Query parameters:
    - q: Search query (required)
    - location: Location for search (optional)
    - gl: Country code (optional)
    - hl: Language code (optional)
    - num: Number of results (optional)

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com")

        if not serpapi_api_key:
            raise HTTPException(status_code=503, detail="SerpAPI key not configured")

        query_params = dict(request.query_params)
        query = query_params.get("q")

        if not query:
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

        logger.info("=" * 80)
        logger.info(f"📥 SERPAPI GOOGLE SHOPPING REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Query: {query}")

        serpapi_url = f"{serpapi_base_url}/search"
        params = {
            "api_key": serpapi_api_key,
            "engine": "google",
            "tbm": "shop",  # Google Shopping
            **query_params
        }

        response = requests.get(serpapi_url, params=params, timeout=config.timeout)
        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ SERPAPI SHOPPING COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Products: {len(result.get('shopping_results', []))}")
        logger.info("=" * 80)

        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/serpapi/shopping',
            input_tokens=len(query),
            output_tokens=len(str(result)),
            model='serpapi-google-shopping',
            request_id=None,
            backend_url=serpapi_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ SERPAPI SHOPPING ERROR: {e}")
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ INTERNAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/v1/serpapi/maps")
async def serpapi_maps(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    SerpAPI Google Maps endpoint - proxy to SerpAPI.

    Searches Google Maps and returns local business results.

    Query parameters:
    - q: Search query (required)
    - location: Location for search (optional but recommended)
    - gl: Country code (optional)
    - hl: Language code (optional)
    - num: Number of results (optional)

    Requires authentication via Bearer token.
    """
    start_time = time.time()

    try:
        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        serpapi_base_url = os.getenv("SERPAPI_BASE_URL", "https://serpapi.com")

        if not serpapi_api_key:
            raise HTTPException(status_code=503, detail="SerpAPI key not configured")

        query_params = dict(request.query_params)
        query = query_params.get("q")

        if not query:
            raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

        logger.info("=" * 80)
        logger.info(f"📥 SERPAPI GOOGLE MAPS REQUEST")
        logger.info(f"User: {user_info['username']} (ID: {user_info['user_id']})")
        logger.info(f"Query: {query}")

        serpapi_url = f"{serpapi_base_url}/search"
        params = {
            "api_key": serpapi_api_key,
            "engine": "google",
            "tbm": "lcl",  # Google Maps/Local
            **query_params
        }

        response = requests.get(serpapi_url, params=params, timeout=config.timeout)
        response.raise_for_status()
        result = response.json()

        elapsed_time = time.time() - start_time
        logger.info(f"✅ SERPAPI MAPS COMPLETED")
        logger.info(f"Duration: {elapsed_time:.2f}s")
        logger.info(f"Local results: {len(result.get('local_results', []))}")
        logger.info("=" * 80)

        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/serpapi/maps',
            input_tokens=len(query),
            output_tokens=len(str(result)),
            model='serpapi-google-maps',
            request_id=None,
            backend_url=serpapi_base_url
        )

        return JSONResponse(content=result)

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ SERPAPI MAPS ERROR: {e}")
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=str(e))

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ INTERNAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/v1/tavily/search")
async def tavily_search(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Tavily AI Search endpoint.

    Proxies requests to Tavily Search API with comprehensive search capabilities.
    """
    start_time = time.time()

    try:
        # Get API key from environment
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise HTTPException(status_code=503, detail="Tavily API key not configured")

        # Parse request body
        body = await request.json()

        # Validate required parameters
        if "query" not in body:
            raise HTTPException(status_code=400, detail="Missing required parameter: query")

        query = body.get("query")

        # Prepare request to Tavily API
        tavily_url = "https://api.tavily.com/search"

        # Build request payload with all parameters
        payload = {
            "api_key": tavily_api_key,
            "query": query
        }

        # Add optional parameters if provided
        optional_params = [
            "auto_parameters", "topic", "search_depth", "chunks_per_source",
            "max_results", "time_range", "start_date", "end_date",
            "include_answer", "include_raw_content", "include_images",
            "include_image_descriptions", "include_favicon",
            "include_domains", "exclude_domains", "country"
        ]

        for param in optional_params:
            if param in body:
                payload[param] = body[param]

        logger.info(f"🔍 TAVILY SEARCH: query='{query}' user={user_info.get('username')}")

        # Make request to Tavily
        response = requests.post(
            tavily_url,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        result = response.json()

        elapsed_time = time.time() - start_time

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/tavily/search',
            input_tokens=len(query),
            output_tokens=len(str(result)),
            model='tavily-search',
            request_id=result.get('request_id'),
            backend_url="https://api.tavily.com/search"
        )

        logger.info(f"✅ TAVILY SEARCH SUCCESS: {len(result.get('results', []))} results in {elapsed_time:.2f}s")

        return result

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        error_detail = str(e)
        if e.response is not None:
            try:
                error_body = e.response.json()
                error_detail = f"{e.response.status_code} {e.response.reason}: {error_body}"
            except:
                error_detail = f"{e.response.status_code} {e.response.reason}"

        logger.error(f"❌ TAVILY SEARCH ERROR: {error_detail}")
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=error_detail)

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ INTERNAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/v1/tavily/extract")
async def tavily_extract(
    request: Request,
    user_info: Dict[str, Any] = Depends(get_current_user)
):
    """
    Tavily Extract endpoint.

    Proxies requests to Tavily Extract API for web content extraction.
    """
    start_time = time.time()

    try:
        # Get API key from environment
        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise HTTPException(status_code=503, detail="Tavily API key not configured")

        # Parse request body
        body = await request.json()

        # Validate required parameters
        if "urls" not in body:
            raise HTTPException(status_code=400, detail="Missing required parameter: urls")

        urls = body.get("urls")
        if isinstance(urls, str):
            urls = [urls]

        if not isinstance(urls, list) or len(urls) == 0:
            raise HTTPException(status_code=400, detail="urls must be a non-empty string or list of strings")

        if len(urls) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 URLs allowed per request")

        # Prepare request to Tavily API
        tavily_url = "https://api.tavily.com/extract"

        # Build request payload
        payload = {
            "api_key": tavily_api_key,
            "urls": urls
        }

        # Add optional parameters if provided
        optional_params = ["include_images", "include_favicon", "extract_depth", "format", "timeout"]

        for param in optional_params:
            if param in body:
                payload[param] = body[param]

        logger.info(f"📄 TAVILY EXTRACT: {len(urls)} URL(s) user={user_info.get('username')}")

        # Make request to Tavily
        response = requests.post(
            tavily_url,
            json=payload,
            timeout=120  # Longer timeout for extraction
        )
        response.raise_for_status()

        result = response.json()

        elapsed_time = time.time() - start_time

        # Track usage
        user_manager.track_usage(
            api_key_id=user_info['api_key_id'],
            endpoint='/v1/tavily/extract',
            input_tokens=len(urls),
            output_tokens=len(str(result)),
            model='tavily-extract',
            request_id=result.get('request_id'),
            backend_url="https://api.tavily.com/extract"
        )

        successful = len(result.get('results', []))
        failed = len(result.get('failed_results', []))
        logger.info(f"✅ TAVILY EXTRACT SUCCESS: {successful} extracted, {failed} failed in {elapsed_time:.2f}s")

        return result

    except requests.exceptions.HTTPError as e:
        elapsed_time = time.time() - start_time
        error_detail = str(e)
        if e.response is not None:
            try:
                error_body = e.response.json()
                error_detail = f"{e.response.status_code} {e.response.reason}: {error_body}"
            except:
                error_detail = f"{e.response.status_code} {e.response.reason}"

        logger.error(f"❌ TAVILY EXTRACT ERROR: {error_detail}")
        raise HTTPException(status_code=e.response.status_code if e.response else 500, detail=error_detail)

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ INTERNAL ERROR: {str(e)}")
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
