"""Configuration management for the OpenAI to Claude proxy."""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class ProxyConfig:
    """Configuration for the proxy server."""

    # OpenAI-compatible backend configuration
    openai_base_url: str
    openai_api_key: str
    openai_model: str

    # Proxy server configuration
    proxy_host: str = "localhost"
    proxy_port: int = 8000

    # Optional settings
    timeout: int = 300  # 5 minutes
    debug: bool = False
    max_input_tokens: int = 200000  # Maximum input tokens
    max_output_tokens: int = 200000  # Maximum output tokens

    @classmethod
    def from_env(cls) -> "ProxyConfig":
        """Load configuration from environment variables."""
        return cls(
            openai_base_url=os.getenv(
                "OPENAI_BASE_URL",
                "https://cloud.infini-ai.com/maas/v1/chat/completions"
            ),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "glm-4.6"),
            proxy_host=os.getenv("PROXY_HOST", "localhost"),
            proxy_port=int(os.getenv("PROXY_PORT", "8000")),
            timeout=int(os.getenv("TIMEOUT", "300")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            max_input_tokens=int(os.getenv("MAX_INPUT_TOKENS", "200000")),
            max_output_tokens=int(os.getenv("MAX_OUTPUT_TOKENS", "200000")),
        )

    def validate(self) -> None:
        """Validate configuration."""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set")
        if not self.openai_base_url:
            raise ValueError("OPENAI_BASE_URL must be set")
        if not self.openai_model:
            raise ValueError("OPENAI_MODEL must be set")
