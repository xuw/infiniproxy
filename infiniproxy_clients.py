#!/usr/bin/env python3
"""
InfiniProxy Client Library - Compatible wrappers for official API clients

This library provides drop-in replacement clients for popular API services
that work seamlessly with InfiniProxy while maintaining interface compatibility
with official client libraries.

Usage:
    from infiniproxy_clients import ElevenLabsClient, TavilyClient

    # Initialize with environment variables or parameters
    elevenlabs = ElevenLabsClient()
    audio = elevenlabs.text_to_speech("Hello world!")

Environment Variables:
    AIAPI_URL: InfiniProxy base URL (default: https://aiapi.iiis.co:9443)
    AIAPI_KEY: InfiniProxy API key (required)
"""

import os
import requests
from typing import Optional, Dict, Any, List, Union
from urllib.parse import urljoin


class ProxyClientError(Exception):
    """Base exception for proxy client errors"""
    pass


class BaseProxyClient:
    """
    Base class for all InfiniProxy-compatible clients

    Attributes:
        api_key: InfiniProxy API key
        base_url: InfiniProxy base URL
        session: Requests session for connection pooling
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize the proxy client

        Args:
            api_key: API key (defaults to AIAPI_KEY env var)
            base_url: Base URL (defaults to AIAPI_URL env var or https://aiapi.iiis.co:9443)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv('AIAPI_KEY') or os.getenv('INFINIPROXY_API_KEY')
        self.base_url = (
            base_url or
            os.getenv('AIAPI_URL') or
            os.getenv('INFINIPROXY_URL') or
            'https://aiapi.iiis.co:9443'
        )
        self.timeout = timeout

        if not self.api_key:
            raise ProxyClientError(
                "API key required. Set AIAPI_KEY environment variable or pass api_key parameter."
            )

        # Initialize session with connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'InfiniProxy-Python-Client/1.0'
        })

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with error handling

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments to pass to requests

        Returns:
            Response object

        Raises:
            ProxyClientError: On request failure
        """
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            raise ProxyClientError(f"HTTP {e.response.status_code}: {e.response.text}")
        except requests.exceptions.Timeout:
            raise ProxyClientError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise ProxyClientError(f"Request failed: {str(e)}")

    def close(self):
        """Close the session"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class ElevenLabsClient(BaseProxyClient):
    """
    InfiniProxy-compatible ElevenLabs client

    Provides text-to-speech and speech-to-text functionality compatible
    with the official ElevenLabs Python client interface.

    Example:
        client = ElevenLabsClient()
        audio = client.text_to_speech("Hello world!")
        with open("output.mp3", "wb") as f:
            f.write(audio)
    """

    def text_to_speech(
        self,
        text: str,
        model_id: str = "eleven_monolingual_v1",
        voice_id: Optional[str] = None,
        voice_settings: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bytes:
        """
        Generate speech audio from text

        Args:
            text: Text to convert to speech
            model_id: ElevenLabs model ID
            voice_id: Voice ID to use
            voice_settings: Voice configuration settings
            **kwargs: Additional parameters

        Returns:
            Audio data as bytes (MP3 format)
        """
        payload = {
            'text': text,
            'model_id': model_id,
        }

        if voice_id:
            payload['voice_id'] = voice_id
        if voice_settings:
            payload['voice_settings'] = voice_settings

        payload.update(kwargs)

        response = self._request('POST', '/v1/elevenlabs/text-to-speech', json=payload)
        return response.content

    def generate(
        self,
        text: str,
        voice: str = "default",
        model: str = "eleven_monolingual_v1",
        **kwargs
    ) -> bytes:
        """
        Alias for text_to_speech with alternative parameter names

        Args:
            text: Text to convert to speech
            voice: Voice name/ID
            model: Model ID
            **kwargs: Additional parameters

        Returns:
            Audio data as bytes
        """
        return self.text_to_speech(
            text=text,
            voice_id=voice,
            model_id=model,
            **kwargs
        )


class SerpAPIClient(BaseProxyClient):
    """
    InfiniProxy-compatible SerpAPI client

    Provides Google search functionality compatible with the official
    google-search-results Python client interface.

    Example:
        client = SerpAPIClient()
        results = client.search("Python programming")
        print(results['organic_results'][0]['title'])
    """

    def search(
        self,
        query: str,
        num: int = 10,
        engine: str = "google",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform search

        Args:
            query: Search query
            num: Number of results
            engine: Search engine (google, bing, etc.)
            **kwargs: Additional search parameters

        Returns:
            Search results dictionary
        """
        params = {
            'q': query,
            'num': num,
            'engine': engine,
            **kwargs
        }

        response = self._request('GET', '/v1/serpapi/search', params=params)
        return response.json()

    def get_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get search results using params dictionary (official client style)

        Args:
            params: Search parameters

        Returns:
            Search results dictionary
        """
        return self.search(**params)


class FirecrawlClient(BaseProxyClient):
    """
    InfiniProxy-compatible Firecrawl client

    Provides web scraping and crawling functionality compatible with
    the official Firecrawl Python client interface.

    Example:
        client = FirecrawlClient()
        result = client.scrape_url("https://example.com")
        print(result['data']['markdown'])
    """

    def scrape_url(
        self,
        url: str,
        formats: Optional[List[str]] = None,
        only_main_content: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scrape a single URL

        Args:
            url: URL to scrape
            formats: Output formats (markdown, html, etc.)
            only_main_content: Extract only main content
            **kwargs: Additional parameters

        Returns:
            Scraping results dictionary
        """
        payload = {
            'url': url,
            'formats': formats or ['markdown', 'html'],
            'onlyMainContent': only_main_content,
            **kwargs
        }

        response = self._request('POST', '/v1/firecrawl/scrape', json=payload)
        return response.json()

    def search(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search the web

        Args:
            query: Search query
            limit: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Search results dictionary
        """
        payload = {
            'query': query,
            'limit': limit,
            **kwargs
        }

        response = self._request('POST', '/v1/firecrawl/search', json=payload)
        return response.json()

    def crawl_url(
        self,
        url: str,
        max_depth: int = 2,
        limit: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Crawl a website

        Args:
            url: Starting URL
            max_depth: Maximum crawl depth
            limit: Maximum number of pages
            **kwargs: Additional parameters

        Returns:
            Crawling results dictionary
        """
        payload = {
            'url': url,
            'maxDepth': max_depth,
            **kwargs
        }

        if limit:
            payload['limit'] = limit

        response = self._request('POST', '/v1/firecrawl/crawl', json=payload)
        return response.json()


class TavilyClient(BaseProxyClient):
    """
    InfiniProxy-compatible Tavily client

    Provides AI-powered search functionality compatible with the
    official Tavily Python client interface.

    Example:
        client = TavilyClient()
        results = client.search("Latest AI news")
        print(results['answer'])
    """

    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_raw_content: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform AI-powered search

        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: Search depth (basic or advanced)
            include_answer: Include AI-generated answer
            include_raw_content: Include raw HTML content
            **kwargs: Additional parameters

        Returns:
            Search results dictionary with answer and sources
        """
        payload = {
            'query': query,
            'max_results': max_results,
            'search_depth': search_depth,
            'include_answer': include_answer,
            'include_raw_content': include_raw_content,
            **kwargs
        }

        response = self._request('POST', '/v1/tavily/search', json=payload)
        return response.json()

    def get_search_context(
        self,
        query: str,
        max_results: int = 5,
        **kwargs
    ) -> str:
        """
        Get search context as a single string

        Args:
            query: Search query
            max_results: Maximum number of results
            **kwargs: Additional parameters

        Returns:
            Concatenated search context
        """
        results = self.search(query, max_results=max_results, **kwargs)
        return results.get('answer', '')

    def qna_search(
        self,
        query: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Question-answering search (alias for search with answer)

        Args:
            query: Question to answer
            **kwargs: Additional parameters

        Returns:
            Search results with answer
        """
        return self.search(query, include_answer=True, **kwargs)


# Convenience factory functions for compatibility

def create_elevenlabs_client(**kwargs) -> ElevenLabsClient:
    """Create ElevenLabs client instance"""
    return ElevenLabsClient(**kwargs)


def create_serpapi_client(**kwargs) -> SerpAPIClient:
    """Create SerpAPI client instance"""
    return SerpAPIClient(**kwargs)


def create_firecrawl_client(**kwargs) -> FirecrawlClient:
    """Create Firecrawl client instance"""
    return FirecrawlClient(**kwargs)


def create_tavily_client(**kwargs) -> TavilyClient:
    """Create Tavily client instance"""
    return TavilyClient(**kwargs)


# Module-level convenience instances (lazy initialization)
_elevenlabs_instance = None
_serpapi_instance = None
_firecrawl_instance = None
_tavily_instance = None


def get_elevenlabs_client() -> ElevenLabsClient:
    """Get or create singleton ElevenLabs client"""
    global _elevenlabs_instance
    if _elevenlabs_instance is None:
        _elevenlabs_instance = ElevenLabsClient()
    return _elevenlabs_instance


def get_serpapi_client() -> SerpAPIClient:
    """Get or create singleton SerpAPI client"""
    global _serpapi_instance
    if _serpapi_instance is None:
        _serpapi_instance = SerpAPIClient()
    return _serpapi_instance


def get_firecrawl_client() -> FirecrawlClient:
    """Get or create singleton Firecrawl client"""
    global _firecrawl_instance
    if _firecrawl_instance is None:
        _firecrawl_instance = FirecrawlClient()
    return _firecrawl_instance


def get_tavily_client() -> TavilyClient:
    """Get or create singleton Tavily client"""
    global _tavily_instance
    if _tavily_instance is None:
        _tavily_instance = TavilyClient()
    return _tavily_instance


__all__ = [
    'ElevenLabsClient',
    'SerpAPIClient',
    'FirecrawlClient',
    'TavilyClient',
    'ProxyClientError',
    'create_elevenlabs_client',
    'create_serpapi_client',
    'create_firecrawl_client',
    'create_tavily_client',
    'get_elevenlabs_client',
    'get_serpapi_client',
    'get_firecrawl_client',
    'get_tavily_client',
]
