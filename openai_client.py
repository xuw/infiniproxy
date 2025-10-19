"""OpenAI API client for making requests to OpenAI-compatible endpoints."""

import requests
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

    def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a chat completion.

        Args:
            request: OpenAI API request payload

        Returns:
            OpenAI API response

        Raises:
            requests.HTTPError: If the request fails
            requests.Timeout: If the request times out
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        logger.info(f"Sending request to {self.base_url}")
        logger.debug(f"Request payload: {request}")

        try:
            response = requests.post(
                self.base_url,
                json=request,
                headers=headers,
                timeout=self.timeout
            )

            logger.info(f"Received response with status code: {response.status_code}")

            # Raise exception for bad status codes
            response.raise_for_status()

            response_data = response.json()
            logger.debug(f"Response data: {response_data}")

            return response_data

        except requests.Timeout as e:
            logger.error(f"Request timed out after {self.timeout} seconds")
            raise

        except requests.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            logger.error(f"Response text: {e.response.text if e.response else 'No response'}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def create_streaming_completion(self, request: Dict[str, Any]):
        """
        Create a streaming chat completion.

        Args:
            request: OpenAI API request payload with stream=True

        Yields:
            Server-sent events in OpenAI format

        Raises:
            requests.HTTPError: If the request fails
            requests.Timeout: If the request times out
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream"
        }

        logger.info(f"Sending streaming request to {self.base_url}")
        logger.debug(f"Request payload: {request}")

        try:
            response = requests.post(
                self.base_url,
                json=request,
                headers=headers,
                timeout=self.timeout,
                stream=True
            )

            logger.info(f"Received streaming response with status code: {response.status_code}")
            response.raise_for_status()

            # Stream the response
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    logger.debug(f"Streaming line: {decoded_line}")
                    yield decoded_line

        except requests.Timeout as e:
            logger.error(f"Streaming request timed out after {self.timeout} seconds")
            raise

        except requests.HTTPError as e:
            logger.error(f"HTTP error in streaming: {e}")
            logger.error(f"Response text: {e.response.text if e.response else 'No response'}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in streaming: {e}")
            raise
