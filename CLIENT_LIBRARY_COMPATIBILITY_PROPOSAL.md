# Client Library Compatibility Proposal

## Problem Statement

Most official third-party API client libraries (ElevenLabs, SerpAPI, Firecrawl, Tavily) are hardcoded to use their service's official base URLs and don't support custom endpoints. This prevents users from transparently using these libraries with InfiniProxy.

**Current Status**:
- ✅ Direct API calls with `requests`: Fully compatible
- ✅ OpenAI/Anthropic SDKs: Support `BASE_URL` environment variables
- ❌ ElevenLabs Python client: No custom base URL support
- ❌ SerpAPI client: Hardcoded to serpapi.com
- ❌ Firecrawl client: Limited/no custom URL support
- ❌ Tavily client: Hardcoded to api.tavily.com

## Proposed Solutions

### Approach 1: HTTP Interceptor Proxy (RECOMMENDED)

**Concept**: Use an HTTP(S) proxy to intercept and redirect requests from official clients to InfiniProxy.

**Implementation Options**:

#### Option 1a: mitmproxy-based Solution
```python
# proxy_interceptor.py
from mitmproxy import http
import os

class InfiniProxyInterceptor:
    """Intercept and redirect API calls to InfiniProxy"""

    DOMAIN_MAPPINGS = {
        'api.elevenlabs.io': os.getenv('AIAPI_URL', 'https://aiapi.iiis.co:9443'),
        'serpapi.com': os.getenv('AIAPI_URL', 'https://aiapi.iiis.co:9443'),
        'api.firecrawl.dev': os.getenv('AIAPI_URL', 'https://aiapi.iiis.co:9443'),
        'api.tavily.com': os.getenv('AIAPI_URL', 'https://aiapi.iiis.co:9443'),
    }

    def request(self, flow: http.HTTPFlow) -> None:
        """Intercept and modify outgoing requests"""

        # Check if request matches known API domains
        for original_domain, proxy_url in self.DOMAIN_MAPPINGS.items():
            if original_domain in flow.request.pretty_host:
                # Extract proxy host and port
                from urllib.parse import urlparse
                parsed = urlparse(proxy_url)

                # Redirect to InfiniProxy
                flow.request.scheme = parsed.scheme
                flow.request.host = parsed.hostname
                flow.request.port = parsed.port or (443 if parsed.scheme == 'https' else 80)

                # Preserve original path but adjust for InfiniProxy routing
                original_path = flow.request.path

                # Map to InfiniProxy endpoint structure
                if 'elevenlabs' in original_domain:
                    flow.request.path = f"/v1/elevenlabs{original_path}"
                elif 'serpapi' in original_domain:
                    flow.request.path = f"/v1/serpapi{original_path}"
                elif 'firecrawl' in original_domain:
                    flow.request.path = f"/v1/firecrawl{original_path}"
                elif 'tavily' in original_domain:
                    flow.request.path = f"/v1/tavily{original_path}"

                # Replace API key in Authorization header if needed
                proxy_api_key = os.getenv('AIAPI_KEY')
                if proxy_api_key:
                    flow.request.headers["Authorization"] = f"Bearer {proxy_api_key}"

                break

addons = [InfiniProxyInterceptor()]
```

**Usage**:
```bash
# Start interceptor proxy
mitmproxy -s proxy_interceptor.py -p 8888

# Configure client to use proxy
export HTTP_PROXY=http://localhost:8888
export HTTPS_PROXY=http://localhost:8888

# Now official clients will be automatically redirected
python client_code.py
```

**Pros**:
- ✅ No modification to client code required
- ✅ Works with all official client libraries
- ✅ Centralized configuration
- ✅ Can intercept and log all API calls
- ✅ Easy to enable/disable (just unset proxy env vars)

**Cons**:
- ❌ Requires running an additional proxy process
- ❌ HTTPS interception requires certificate trust setup
- ❌ Additional latency (proxy hop)
- ❌ Complexity in debugging

#### Option 1b: Local DNS Override
```bash
# /etc/hosts modifications (requires sudo)
127.0.0.1  api.elevenlabs.io
127.0.0.1  serpapi.com
127.0.0.1  api.firecrawl.dev
127.0.0.1  api.tavily.com

# Then run local reverse proxy
# nginx.conf
server {
    listen 443 ssl;
    server_name api.elevenlabs.io serpapi.com api.firecrawl.dev api.tavily.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass https://aiapi.iiis.co:9443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Pros**:
- ✅ System-wide redirection
- ✅ No code changes needed

**Cons**:
- ❌ Requires root/admin access
- ❌ Affects all applications on system
- ❌ Complex SSL certificate management
- ❌ Hard to maintain across multiple developers

---

### Approach 2: Monkey Patching Library

**Concept**: Create a Python library that monkey-patches official client libraries at import time.

```python
# infiniproxy_patcher.py
"""Monkey-patch official client libraries to support InfiniProxy"""

import os
import sys
from typing import Optional
from urllib.parse import urlparse

class InfiniProxyPatcher:
    """Patches official client libraries to use InfiniProxy"""

    def __init__(self, proxy_url: Optional[str] = None, proxy_api_key: Optional[str] = None):
        self.proxy_url = proxy_url or os.getenv('AIAPI_URL', 'https://aiapi.iiis.co:9443')
        self.proxy_api_key = proxy_api_key or os.getenv('AIAPI_KEY')

        if not self.proxy_api_key:
            raise ValueError("AIAPI_KEY environment variable or proxy_api_key parameter required")

    def patch_elevenlabs(self):
        """Patch ElevenLabs client library"""
        try:
            import elevenlabs
            from elevenlabs.client import ElevenLabs

            original_init = ElevenLabs.__init__

            def patched_init(self, api_key=None, *args, **kwargs):
                # Override base_url
                kwargs['base_url'] = f"{self.proxy_url}/v1/elevenlabs"
                # Use proxy API key
                api_key = self.proxy_api_key
                return original_init(self, api_key=api_key, *args, **kwargs)

            ElevenLabs.__init__ = patched_init
            print("✓ ElevenLabs client patched for InfiniProxy")

        except ImportError:
            pass  # Library not installed

    def patch_serpapi(self):
        """Patch SerpAPI client library"""
        try:
            import serpapi
            from serpapi import GoogleSearch

            # SerpAPI uses requests internally, patch the URL building
            original_get_results = GoogleSearch.get_results

            def patched_get_results(self):
                # Override the API endpoint
                self.SERP_API_ENDPOINT = f"{self.proxy_url}/v1/serpapi/search"
                return original_get_results(self)

            GoogleSearch.get_results = patched_get_results
            print("✓ SerpAPI client patched for InfiniProxy")

        except ImportError:
            pass

    def patch_firecrawl(self):
        """Patch Firecrawl client library"""
        try:
            from firecrawl import FirecrawlApp

            original_init = FirecrawlApp.__init__

            def patched_init(self, api_key=None, api_url=None):
                # Override API URL
                api_url = f"{self.proxy_url}/v1/firecrawl"
                api_key = self.proxy_api_key
                return original_init(self, api_key=api_key, api_url=api_url)

            FirecrawlApp.__init__ = patched_init
            print("✓ Firecrawl client patched for InfiniProxy")

        except ImportError:
            pass

    def patch_tavily(self):
        """Patch Tavily client library"""
        try:
            from tavily import TavilyClient

            original_init = TavilyClient.__init__

            def patched_init(self, api_key=None):
                self._api_key = self.proxy_api_key
                self._base_url = f"{self.proxy_url}/v1/tavily"
                # Call original but override base URL after
                result = original_init(self, api_key=api_key)
                self.base_url = self._base_url
                return result

            TavilyClient.__init__ = patched_init
            print("✓ Tavily client patched for InfiniProxy")

        except ImportError:
            pass

    def patch_all(self):
        """Patch all supported client libraries"""
        self.patch_elevenlabs()
        self.patch_serpapi()
        self.patch_firecrawl()
        self.patch_tavily()

# Auto-patch on import if INFINIPROXY_AUTO_PATCH is set
if os.getenv('INFINIPROXY_AUTO_PATCH', '').lower() in ('1', 'true', 'yes'):
    patcher = InfiniProxyPatcher()
    patcher.patch_all()
```

**Usage**:
```python
# Option 1: Manual patching
from infiniproxy_patcher import InfiniProxyPatcher

patcher = InfiniProxyPatcher()
patcher.patch_all()

# Now use official clients normally
from elevenlabs.client import ElevenLabs
client = ElevenLabs()  # Will use InfiniProxy automatically

# Option 2: Auto-patching via environment variable
# export INFINIPROXY_AUTO_PATCH=1
import infiniproxy_patcher  # Patches applied automatically
from elevenlabs.client import ElevenLabs
client = ElevenLabs()
```

**Pros**:
- ✅ No changes to client code after patching
- ✅ Works with official client libraries
- ✅ Can be toggled via environment variable
- ✅ Python-native solution

**Cons**:
- ❌ Fragile (breaks when client libraries update)
- ❌ Requires deep knowledge of each client's internals
- ❌ Python-only (doesn't help Node.js, etc.)
- ❌ Maintenance burden for each client library version

---

### Approach 3: Wrapper Library (RECOMMENDED for Production)

**Concept**: Create thin wrapper classes that provide the same interface as official clients but use direct API calls.

```python
# infiniproxy_clients.py
"""
InfiniProxy-compatible client wrappers with official client interfaces
"""

import os
import requests
from typing import Optional, Dict, Any, List

class BaseProxyClient:
    """Base class for proxy-compatible clients"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv('AIAPI_KEY')
        self.base_url = base_url or os.getenv('AIAPI_URL', 'https://aiapi.iiis.co:9443')

        if not self.api_key:
            raise ValueError("API key required (AIAPI_KEY env var or api_key parameter)")

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })

class ElevenLabsClient(BaseProxyClient):
    """InfiniProxy-compatible ElevenLabs client with official-like interface"""

    def text_to_speech(self, text: str, model_id: str = "eleven_monolingual_v1",
                       voice_id: Optional[str] = None, **kwargs) -> bytes:
        """Generate speech from text"""

        url = f"{self.base_url}/v1/elevenlabs/text-to-speech"
        payload = {
            'text': text,
            'model_id': model_id,
            'voice_id': voice_id,
            **kwargs
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.content

    def generate(self, text: str, voice: str = "default", **kwargs) -> bytes:
        """Alias for text_to_speech with voice parameter"""
        return self.text_to_speech(text, voice_id=voice, **kwargs)

class SerpAPIClient(BaseProxyClient):
    """InfiniProxy-compatible SerpAPI client with official-like interface"""

    def search(self, query: str, num: int = 10, **kwargs) -> Dict[str, Any]:
        """Perform Google search"""

        url = f"{self.base_url}/v1/serpapi/search"
        params = {
            'q': query,
            'num': num,
            **kwargs
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get search results with params dict (official client style)"""
        return self.search(**params)

class FirecrawlClient(BaseProxyClient):
    """InfiniProxy-compatible Firecrawl client with official-like interface"""

    def scrape_url(self, url: str, formats: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Scrape a URL"""

        api_url = f"{self.base_url}/v1/firecrawl/scrape"
        payload = {
            'url': url,
            'formats': formats or ['markdown', 'html'],
            **kwargs
        }

        response = self.session.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """Search the web"""

        api_url = f"{self.base_url}/v1/firecrawl/search"
        payload = {
            'query': query,
            'limit': limit,
            **kwargs
        }

        response = self.session.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()

    def crawl_url(self, url: str, max_depth: int = 2, **kwargs) -> Dict[str, Any]:
        """Crawl a website"""

        api_url = f"{self.base_url}/v1/firecrawl/crawl"
        payload = {
            'url': url,
            'max_depth': max_depth,
            **kwargs
        }

        response = self.session.post(api_url, json=payload)
        response.raise_for_status()
        return response.json()

class TavilyClient(BaseProxyClient):
    """InfiniProxy-compatible Tavily client with official-like interface"""

    def search(self, query: str, max_results: int = 5,
               search_depth: str = "basic", **kwargs) -> Dict[str, Any]:
        """Perform AI-powered search"""

        url = f"{self.base_url}/v1/tavily/search"
        payload = {
            'query': query,
            'max_results': max_results,
            'search_depth': search_depth,
            **kwargs
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_search_context(self, query: str, **kwargs) -> str:
        """Get search context as string"""
        results = self.search(query, **kwargs)
        return results.get('answer', '')

# Convenience functions for drop-in replacement
def create_elevenlabs_client(**kwargs) -> ElevenLabsClient:
    """Create ElevenLabs client"""
    return ElevenLabsClient(**kwargs)

def create_serpapi_client(**kwargs) -> SerpAPIClient:
    """Create SerpAPI client"""
    return SerpAPIClient(**kwargs)

def create_firecrawl_client(**kwargs) -> FirecrawlClient:
    """Create Firecrawl client"""
    return FirecrawlClient(**kwargs)

def create_tavily_client(**kwargs) -> TavilyClient:
    """Create Tavily client"""
    return TavilyClient(**kwargs)
```

**Usage**:
```python
# Replace official client imports
# from elevenlabs.client import ElevenLabs
from infiniproxy_clients import ElevenLabsClient as ElevenLabs

# Use like official client
client = ElevenLabs()
audio = client.text_to_speech("Hello world!")

# Or use convenience functions
from infiniproxy_clients import create_elevenlabs_client
client = create_elevenlabs_client()
```

**Pros**:
- ✅ Clean, maintainable Python code
- ✅ Similar interface to official clients
- ✅ Type hints and documentation
- ✅ Easy to extend with new features
- ✅ Robust and testable
- ✅ No fragile monkey-patching

**Cons**:
- ❌ Requires code changes to import wrapper instead of official client
- ❌ Not a perfect drop-in replacement
- ❌ May miss some advanced features of official clients

---

### Approach 4: Environment Variable Injection via sitecustomize

**Concept**: Use Python's `sitecustomize.py` to auto-patch libraries on interpreter startup.

```python
# sitecustomize.py (place in Python's site-packages or set PYTHONPATH)
"""
Auto-configure InfiniProxy for all Python sessions
Place in site-packages or set PYTHONPATH to directory containing this file
"""

import os
import sys

# Only activate if INFINIPROXY_ENABLED is set
if os.getenv('INFINIPROXY_ENABLED', '').lower() in ('1', 'true', 'yes'):

    # Import patcher after modules are available
    def patch_on_import():
        try:
            from infiniproxy_patcher import InfiniProxyPatcher
            patcher = InfiniProxyPatcher()
            patcher.patch_all()
            print("✓ InfiniProxy auto-patching enabled", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  InfiniProxy auto-patch failed: {e}", file=sys.stderr)

    # Delay patching until first import
    import sys

    class ImportHook:
        def find_module(self, name, path=None):
            if name in ['elevenlabs', 'serpapi', 'firecrawl', 'tavily']:
                return self
            return None

        def load_module(self, name):
            if name in sys.modules:
                return sys.modules[name]

            # Import normally
            import importlib
            mod = importlib.import_module(name)

            # Patch after first import
            patch_on_import()

            return mod

    sys.meta_path.insert(0, ImportHook())
```

**Usage**:
```bash
# Enable global auto-patching
export INFINIPROXY_ENABLED=1
export PYTHONPATH=/path/to/infiniproxy/lib:$PYTHONPATH

# Now all Python scripts automatically use InfiniProxy
python any_script.py
```

**Pros**:
- ✅ Zero code changes required
- ✅ System-wide Python configuration
- ✅ Can be toggled via environment variable

**Cons**:
- ❌ Very invasive (affects all Python scripts)
- ❌ Hard to debug when things go wrong
- ❌ May interfere with other tools
- ❌ Not suitable for production

---

### Approach 5: Request Library Patching

**Concept**: Patch the `requests` library (used by most Python clients internally) to redirect specific domains.

```python
# infiniproxy_requests_patch.py
"""Patch requests library to redirect API calls to InfiniProxy"""

import os
import requests
from urllib.parse import urlparse, urlunparse
from functools import wraps

# Store original request methods
_original_request = requests.Session.request

def patched_request(self, method, url, **kwargs):
    """Intercept and redirect requests to InfiniProxy"""

    proxy_url = os.getenv('AIAPI_URL', 'https://aiapi.iiis.co:9443')
    proxy_api_key = os.getenv('AIAPI_KEY')

    # Parse the URL
    parsed = urlparse(url)

    # Domain redirection mapping
    redirects = {
        'api.elevenlabs.io': ('/v1/elevenlabs', True),
        'serpapi.com': ('/v1/serpapi', True),
        'api.firecrawl.dev': ('/v1/firecrawl', True),
        'api.tavily.com': ('/v1/tavily', True),
    }

    # Check if this domain should be redirected
    for domain, (prefix, should_redirect) in redirects.items():
        if domain in parsed.netloc:
            # Redirect to InfiniProxy
            proxy_parsed = urlparse(proxy_url)

            # Construct new URL
            new_path = prefix + parsed.path
            new_url = urlunparse((
                proxy_parsed.scheme,
                f"{proxy_parsed.hostname}:{proxy_parsed.port}" if proxy_parsed.port else proxy_parsed.hostname,
                new_path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            # Update authorization header
            if proxy_api_key:
                headers = kwargs.get('headers', {})
                headers['Authorization'] = f'Bearer {proxy_api_key}'
                kwargs['headers'] = headers

            url = new_url
            break

    # Call original request
    return _original_request(self, method, url, **kwargs)

def enable_infiniproxy_redirect():
    """Enable InfiniProxy request redirection"""
    requests.Session.request = patched_request
    print("✓ InfiniProxy request redirection enabled")

def disable_infiniproxy_redirect():
    """Disable InfiniProxy request redirection"""
    requests.Session.request = _original_request
    print("✓ InfiniProxy request redirection disabled")

# Auto-enable if environment variable set
if os.getenv('INFINIPROXY_REDIRECT', '').lower() in ('1', 'true', 'yes'):
    enable_infiniproxy_redirect()
```

**Usage**:
```python
# Option 1: Manual enable
import infiniproxy_requests_patch
infiniproxy_requests_patch.enable_infiniproxy_redirect()

# Now all requests-based clients are redirected
from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key="dummy")  # Will use InfiniProxy

# Option 2: Auto-enable via environment
# export INFINIPROXY_REDIRECT=1
import infiniproxy_requests_patch  # Auto-enabled
```

**Pros**:
- ✅ Works with any client using `requests` library
- ✅ Minimal code changes (one import)
- ✅ Can be toggled on/off
- ✅ Centralized redirection logic

**Cons**:
- ❌ Only works for Python requests-based clients
- ❌ May affect unintended requests
- ❌ Fragile if clients use httpx or other HTTP libraries
- ❌ Hard to debug unexpected redirections

---

## Comparison Matrix

| Approach | Ease of Use | Compatibility | Maintenance | Production Ready | Language Support |
|----------|-------------|---------------|-------------|------------------|------------------|
| **HTTP Proxy (mitmproxy)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | All languages |
| **DNS Override** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | All languages |
| **Monkey Patching** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Python only |
| **Wrapper Library** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Per language |
| **sitecustomize** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | Python only |
| **Requests Patching** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | Python only |

## Recommended Implementation Strategy

### Phase 1: Quick Win (1-2 days)
**Implement Wrapper Library**
- Create `infiniproxy_clients.py` with wrapper classes
- Publish as `infiniproxy-clients` package on PyPI
- Provide clear migration guide
- **Users**: Install package and update imports

### Phase 2: Advanced Support (1 week)
**Implement HTTP Interceptor Proxy**
- Create mitmproxy-based interceptor
- Package as Docker container for easy deployment
- Provide configuration templates
- **Users**: Run proxy and set HTTP_PROXY env vars

### Phase 3: Ecosystem Integration (Ongoing)
**Contribute to Upstream Projects**
- Submit PRs to official client libraries adding `base_url` parameter
- ElevenLabs, Firecrawl, Tavily, SerpAPI
- This is the long-term sustainable solution
- **Users**: Wait for official support in future releases

## Implementation Priorities

1. **✅ NOW**: Document direct API call patterns (already done)
2. **🎯 NEXT**: Create wrapper library (recommended)
3. **📦 SOON**: Package interceptor proxy solution
4. **🚀 LATER**: Contribute upstream to client libraries

## Example Usage After Implementation

### With Wrapper Library:
```python
# Before
from elevenlabs.client import ElevenLabs
from tavily import TavilyClient

# After (minimal change)
from infiniproxy_clients import ElevenLabsClient as ElevenLabs
from infiniproxy_clients import TavilyClient

# Rest of code unchanged
client = ElevenLabs()
audio = client.text_to_speech("Hello!")
```

### With HTTP Proxy:
```python
# No code changes needed!
# Just run: docker run -d infiniproxy/interceptor
# And set: export HTTPS_PROXY=http://localhost:8888

from elevenlabs.client import ElevenLabs
client = ElevenLabs()  # Automatically uses InfiniProxy
```

## Next Steps

1. **Decision**: Choose primary approach (recommend Wrapper + HTTP Proxy)
2. **Implementation**: Build wrapper library first (highest ROI)
3. **Testing**: Comprehensive compatibility tests
4. **Documentation**: Clear migration guides
5. **Distribution**: Publish to PyPI, Docker Hub
6. **Community**: Engage with upstream projects for long-term solution
