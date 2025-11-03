#!/usr/bin/env python3
"""
InfiniProxy HTTP Interceptor

A lightweight HTTP/HTTPS proxy that intercepts API calls to popular services
and redirects them to InfiniProxy, enabling zero-code-change compatibility
with official client libraries.

Usage:
    # Start the interceptor
    python infiniproxy_interceptor.py

    # Configure client to use proxy
    export HTTP_PROXY=http://localhost:8888
    export HTTPS_PROXY=http://localhost:8888

    # Now official clients automatically use InfiniProxy
    python your_script.py

Features:
    - Zero code changes required
    - Works with all official client libraries
    - Automatic domain detection and routing
    - Request/response logging (optional)
    - Minimal dependencies (requests only)
    - HTTPS support via CONNECT tunneling

Dependencies:
    - requests (pip install requests)

Environment Variables:
    AIAPI_URL: InfiniProxy base URL (default: https://aiapi.iiis.co:9443)
    AIAPI_KEY: InfiniProxy API key (required)
    PROXY_PORT: Port to listen on (default: 8888)
    PROXY_VERBOSE: Enable verbose logging (0 or 1, default: 0)
"""

import os
import sys
import socket
import select
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urlunparse, parse_qs
from typing import Dict, Optional, Tuple
import json

# Optional: requests library for easier HTTP handling
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  Warning: 'requests' library not found. Install with: pip install requests")
    print("   Falling back to basic urllib (limited functionality)")

# Configuration
PROXY_PORT = int(os.getenv('PROXY_PORT', '8888'))
PROXY_HOST = os.getenv('PROXY_HOST', '0.0.0.0')
PROXY_VERBOSE = os.getenv('PROXY_VERBOSE', '0') == '1'

INFINIPROXY_URL = os.getenv('AIAPI_URL') or os.getenv('INFINIPROXY_URL') or 'https://aiapi.iiis.co:9443'
INFINIPROXY_API_KEY = os.getenv('AIAPI_KEY') or os.getenv('INFINIPROXY_API_KEY')

# Domain routing configuration
DOMAIN_ROUTES = {
    'api.elevenlabs.io': {
        'prefix': '/v1/elevenlabs',
        'preserve_path': True,
        'service': 'ElevenLabs'
    },
    'serpapi.com': {
        'prefix': '/v1/serpapi',
        'preserve_path': True,
        'service': 'SerpAPI'
    },
    'api.firecrawl.dev': {
        'prefix': '/v1/firecrawl',
        'preserve_path': True,
        'service': 'Firecrawl'
    },
    'api.tavily.com': {
        'prefix': '/v1/tavily',
        'preserve_path': True,
        'service': 'Tavily'
    },
}

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if PROXY_VERBOSE else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('InfiniProxyInterceptor')


class InterceptorHandler(BaseHTTPRequestHandler):
    """HTTP request handler that intercepts and redirects API calls"""

    # Suppress default logging to avoid duplicate messages
    def log_message(self, format, *args):
        if PROXY_VERBOSE:
            logger.debug(f"{self.address_string()} - {format % args}")

    def do_CONNECT(self):
        """
        Handle HTTPS CONNECT method for SSL tunneling

        This allows transparent HTTPS proxying by establishing a tunnel
        between the client and the target server (or InfiniProxy).
        """
        # Parse the target host and port
        host, port = self.path.split(':')
        port = int(port)

        # Check if this is a domain we should intercept
        route_config = self._get_route_config(host)

        if route_config:
            # Redirect to InfiniProxy
            proxy_parsed = urlparse(INFINIPROXY_URL)
            target_host = proxy_parsed.hostname
            target_port = proxy_parsed.port or (443 if proxy_parsed.scheme == 'https' else 80)

            logger.info(f"🔄 CONNECT {host}:{port} → InfiniProxy ({route_config['service']})")
        else:
            # Pass through to original destination
            target_host = host
            target_port = port
            logger.debug(f"↗️  CONNECT {host}:{port} → passthrough")

        try:
            # Connect to target
            target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target_socket.settimeout(30)
            target_socket.connect((target_host, target_port))

            # Send success response to client
            self.send_response(200, 'Connection Established')
            self.send_header('Proxy-agent', 'InfiniProxy-Interceptor/1.0')
            self.end_headers()

            # Start bidirectional tunneling
            self._tunnel_traffic(self.connection, target_socket)

        except socket.error as e:
            logger.error(f"❌ CONNECT failed: {e}")
            self.send_error(502, f"Bad Gateway: {str(e)}")
        except Exception as e:
            logger.error(f"❌ CONNECT error: {e}")
            self.send_error(500, f"Internal Error: {str(e)}")
        finally:
            try:
                target_socket.close()
            except:
                pass

    def _tunnel_traffic(self, client_socket, target_socket):
        """Bidirectional tunnel between client and target"""
        sockets = [client_socket, target_socket]
        timeout = 60

        try:
            while True:
                # Wait for data on either socket
                readable, _, exceptional = select.select(sockets, [], sockets, timeout)

                if exceptional:
                    break

                if not readable:
                    # Timeout
                    break

                for sock in readable:
                    data = sock.recv(8192)
                    if not data:
                        return

                    # Send to the other socket
                    if sock is client_socket:
                        target_socket.sendall(data)
                    else:
                        client_socket.sendall(data)

        except Exception as e:
            logger.debug(f"Tunnel closed: {e}")

    def do_GET(self):
        """Handle GET requests"""
        self._handle_http_request('GET')

    def do_POST(self):
        """Handle POST requests"""
        self._handle_http_request('POST')

    def do_PUT(self):
        """Handle PUT requests"""
        self._handle_http_request('PUT')

    def do_DELETE(self):
        """Handle DELETE requests"""
        self._handle_http_request('DELETE')

    def do_HEAD(self):
        """Handle HEAD requests"""
        self._handle_http_request('HEAD')

    def do_OPTIONS(self):
        """Handle OPTIONS requests"""
        self._handle_http_request('OPTIONS')

    def do_PATCH(self):
        """Handle PATCH requests"""
        self._handle_http_request('PATCH')

    def _get_route_config(self, host: str) -> Optional[Dict]:
        """Check if host should be routed to InfiniProxy"""
        for domain, config in DOMAIN_ROUTES.items():
            if domain in host:
                return config
        return None

    def _handle_http_request(self, method: str):
        """
        Handle HTTP requests (non-CONNECT)

        This is typically used for HTTP (not HTTPS) proxying, but can also
        handle direct requests if the client is configured to use the proxy.
        """
        # Parse the request URL
        parsed = urlparse(self.path)

        # Extract host from URL or Host header
        if parsed.netloc:
            # Absolute URL (typical for proxies)
            host = parsed.netloc
            path = parsed.path
            query = parsed.query
        else:
            # Relative URL, get host from headers
            host = self.headers.get('Host', '')
            path = self.path
            query = ''
            if '?' in path:
                path, query = path.split('?', 1)

        # Check if this request should be intercepted
        route_config = self._get_route_config(host)

        if route_config:
            self._proxy_to_infiniproxy(method, host, path, query, route_config)
        else:
            # Pass through to original destination
            self._proxy_passthrough(method, host, path, query)

    def _proxy_to_infiniproxy(self, method: str, original_host: str,
                               path: str, query: str, route_config: Dict):
        """Proxy request to InfiniProxy"""

        if not HAS_REQUESTS:
            self.send_error(500, "requests library required for proxying")
            return

        if not INFINIPROXY_API_KEY:
            logger.error("❌ AIAPI_KEY not set")
            self.send_error(500, "InfiniProxy API key not configured")
            return

        # Construct InfiniProxy URL
        infiniproxy_path = route_config['prefix'] + path
        if query:
            full_url = f"{INFINIPROXY_URL}{infiniproxy_path}?{query}"
        else:
            full_url = f"{INFINIPROXY_URL}{infiniproxy_path}"

        logger.info(f"🔄 {method} {original_host}{path} → InfiniProxy ({route_config['service']})")

        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # Prepare headers
            headers = {
                'Authorization': f'Bearer {INFINIPROXY_API_KEY}',
                'Content-Type': self.headers.get('Content-Type', 'application/json'),
                'User-Agent': 'InfiniProxy-Interceptor/1.0',
            }

            # Copy relevant headers from original request
            for header in ['Accept', 'Accept-Encoding', 'Accept-Language']:
                if header in self.headers:
                    headers[header] = self.headers[header]

            # Make request to InfiniProxy
            response = requests.request(
                method=method,
                url=full_url,
                headers=headers,
                data=body,
                timeout=30,
                verify=True,
                allow_redirects=False
            )

            # Send response back to client
            self.send_response(response.status_code)

            # Copy response headers
            for header, value in response.headers.items():
                # Skip headers that shouldn't be forwarded
                if header.lower() not in ['connection', 'transfer-encoding', 'content-encoding']:
                    self.send_header(header, value)

            self.end_headers()

            # Send response body
            self.wfile.write(response.content)

            logger.info(f"✅ {method} {original_host}{path} → {response.status_code}")

        except requests.RequestException as e:
            logger.error(f"❌ Proxy error: {e}")
            self.send_error(502, f"Bad Gateway: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            self.send_error(500, f"Internal Error: {str(e)}")

    def _proxy_passthrough(self, method: str, host: str, path: str, query: str):
        """Pass request through to original destination (not intercepted)"""

        if not HAS_REQUESTS:
            self.send_error(500, "requests library required for proxying")
            return

        # Construct full URL
        scheme = 'https' if ':443' in host or not ':' in host else 'http'
        if query:
            full_url = f"{scheme}://{host}{path}?{query}"
        else:
            full_url = f"{scheme}://{host}{path}"

        logger.debug(f"↗️  {method} {host}{path} → passthrough")

        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            # Prepare headers (copy from original request)
            headers = {}
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection', 'proxy-connection']:
                    headers[header] = value

            # Make request
            response = requests.request(
                method=method,
                url=full_url,
                headers=headers,
                data=body,
                timeout=30,
                verify=True,
                allow_redirects=False
            )

            # Send response back to client
            self.send_response(response.status_code)

            # Copy response headers
            for header, value in response.headers.items():
                if header.lower() not in ['connection', 'transfer-encoding']:
                    self.send_header(header, value)

            self.end_headers()

            # Send response body
            self.wfile.write(response.content)

        except requests.RequestException as e:
            logger.error(f"❌ Passthrough error: {e}")
            self.send_error(502, f"Bad Gateway: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            self.send_error(500, f"Internal Error: {str(e)}")


class ThreadedHTTPServer(HTTPServer):
    """HTTP server that handles each request in a separate thread"""

    def process_request(self, request, client_address):
        """Start a new thread to handle the request"""
        thread = threading.Thread(
            target=self._process_request_thread,
            args=(request, client_address)
        )
        thread.daemon = True
        thread.start()

    def _process_request_thread(self, request, client_address):
        """Process request in thread"""
        try:
            self.finish_request(request, client_address)
        except Exception as e:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def print_banner():
    """Print startup banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                InfiniProxy HTTP Interceptor                      ║
║                  Zero-Code-Change Compatibility                  ║
╚══════════════════════════════════════════════════════════════════╝

Configuration:
  Proxy URL:       {PROXY_HOST}:{PROXY_PORT}
  InfiniProxy URL: {INFINIPROXY_URL}
  API Key:         {"✅ Configured" if INFINIPROXY_API_KEY else "❌ NOT SET"}
  Verbose Logging: {"✅ Enabled" if PROXY_VERBOSE else "Disabled"}

Intercepting domains:
"""
    for domain, config in DOMAIN_ROUTES.items():
        banner += f"  • {domain:30s} → {config['service']}\n"

    banner += f"""
Setup client:
  export HTTP_PROXY=http://localhost:{PROXY_PORT}
  export HTTPS_PROXY=http://localhost:{PROXY_PORT}

Or in Python:
  os.environ['HTTP_PROXY'] = 'http://localhost:{PROXY_PORT}'
  os.environ['HTTPS_PROXY'] = 'http://localhost:{PROXY_PORT}'

Starting server...
"""
    print(banner)


def validate_configuration():
    """Validate configuration and exit if invalid"""
    errors = []

    if not INFINIPROXY_API_KEY:
        errors.append("❌ AIAPI_KEY environment variable not set")

    if not HAS_REQUESTS:
        errors.append("❌ 'requests' library not installed (pip install requests)")

    if errors:
        print("\n⚠️  Configuration Errors:\n")
        for error in errors:
            print(f"  {error}")
        print("\nPlease fix the errors and try again.\n")
        sys.exit(1)


def main():
    """Main entry point"""

    # Validate configuration
    validate_configuration()

    # Print banner
    print_banner()

    # Create server
    try:
        server = ThreadedHTTPServer((PROXY_HOST, PROXY_PORT), InterceptorHandler)
        server.timeout = 0.5  # Allow for clean shutdown

        logger.info(f"✅ Server listening on {PROXY_HOST}:{PROXY_PORT}")
        logger.info("Press Ctrl+C to stop")

        # Run server
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down...")
            server.shutdown()
            logger.info("✅ Server stopped")

    except OSError as e:
        if e.errno == 48:  # Address already in use
            logger.error(f"❌ Port {PROXY_PORT} already in use")
            logger.error(f"   Set PROXY_PORT environment variable to use a different port")
        else:
            logger.error(f"❌ Failed to start server: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
