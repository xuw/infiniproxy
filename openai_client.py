"""OpenAI API client for making requests to OpenAI-compatible endpoints."""

import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for making requests to OpenAI-compatible API endpoints."""

    def __init__(self, base_url: str, api_key: str, timeout: int = 300):
        """
        Initialize OpenAI client.

        Args:
            base_url: Base URL for the OpenAI-compatible API
            api_key: API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        # Create async client with connection pooling for concurrency
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=200, max_connections=250)
        )

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a chat completion (async).

        Args:
            request: OpenAI API request payload

        Returns:
            OpenAI API response

        Raises:
            httpx.HTTPError: If the request fails
            httpx.TimeoutException: If the request times out
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        logger.info(f"Sending async request to {self.base_url}")
        logger.debug(f"Request payload: {request}")

        try:
            response = await self.client.post(
                self.base_url,
                json=request,
                headers=headers
            )

            logger.info(f"Received response with status code: {response.status_code}")

            # Raise exception for bad status codes
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Response data: {response_data}")

            return response_data

        except httpx.TimeoutException as e:
            logger.error(f"Request timed out after {self.timeout} seconds")
            raise

        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            logger.error(f"Response text: {e.response.text if hasattr(e, 'response') and e.response else 'No response'}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def create_streaming_completion(self, request: Dict[str, Any]):
        """
        Create a streaming chat completion (async).

        Args:
            request: OpenAI API request payload with stream=True

        Yields:
            Server-sent events in OpenAI format

        Raises:
            httpx.HTTPError: If the request fails
            httpx.TimeoutException: If the request times out
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream"
        }

        logger.info(f"Sending async streaming request to {self.base_url}")
        logger.debug(f"Request payload: {request}")

        try:
            async with self.client.stream(
                "POST",
                self.base_url,
                json=request,
                headers=headers
            ) as response:
                logger.info(f"Received streaming response with status code: {response.status_code}")
                response.raise_for_status()

                # Stream the response
                async for line in response.aiter_lines():
                    if line:
                        logger.debug(f"Streaming line: {line}")
                        yield line

        except httpx.TimeoutException as e:
            logger.error(f"Streaming request timed out after {self.timeout} seconds")
            raise

        except httpx.HTTPError as e:
            logger.error(f"HTTP error in streaming: {e}")
            logger.error(f"Response text: {e.response.text if hasattr(e, 'response') and e.response else 'No response'}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in streaming: {e}")
            raise

    async def close(self):
        """Close the async client."""
        await self.client.aclose()
