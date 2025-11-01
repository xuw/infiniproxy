# Migration Guide: Environment Variable Changes

## Summary of Changes

The proxy client configuration scripts have been updated to use standardized environment variable names:

**Old Variables** → **New Variables**
- `INFINIPROXY_HOST` → `AIAPI_URL`
- `INFINIPROXY_API_KEY` → `AIAPI_KEY`
- Hardcoded defaults → **No hardcoded defaults** (must be explicitly set)

## Why This Change?

1. **No Hardcoded Credentials**: The new approach requires explicit configuration, improving security
2. **Clearer Naming**: `AIAPI_URL` and `AIAPI_KEY` are more intuitive and consistent
3. **Full URL Support**: `AIAPI_URL` includes the protocol (http/https), eliminating ambiguity
4. **Standardization**: Aligns with common naming conventions for API configuration

## Migration Steps

### Option 1: Update Environment Variables (Recommended)

**Before:**
```bash
# Old approach with positional argument
source set_proxy_env.sh api.example.com
```

**After:**
```bash
# New approach with environment variables
export AIAPI_URL=https://api.example.com
export AIAPI_KEY=your-api-key-here
source set_proxy_env.sh
```

### Option 2: Update .env Files

**Before (`proxy.env`):**
```bash
INFINIPROXY_URL=http://localhost:8000
INFINIPROXY_API_KEY=sk-abc123...
```

**After (`proxy.env`):**
```bash
AIAPI_URL=http://localhost:8000
AIAPI_KEY=sk-abc123...
```

### Option 3: Update Docker Compose

**Before:**
```yaml
environment:
  - INFINIPROXY_URL=http://localhost:8000
  - INFINIPROXY_API_KEY=${PROXY_API_KEY}
```

**After:**
```yaml
environment:
  - AIAPI_URL=http://localhost:8000
  - AIAPI_KEY=${PROXY_API_KEY}
```

### Option 4: Update Python Code

**Before:**
```python
from set_proxy_env import configure_proxy

# Old: Pass host as parameter
config = configure_proxy("api.example.com")
```

**After:**
```python
import os
from set_proxy_env import configure_proxy

# New: Set environment variables first
os.environ["AIAPI_URL"] = "https://api.example.com"
os.environ["AIAPI_KEY"] = "your-api-key"

# Then configure (no parameters)
config = configure_proxy()
```

## What Stays the Same

The following environment variables are **still set automatically** by the scripts and don't need to change:

- `OPENAI_API_BASE` / `OPENAI_BASE_URL` / `OPENAI_API_KEY`
- `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_URL` / `ANTHROPIC_API_KEY`
- `FIRECRAWL_BASE_URL` / `FIRECRAWL_API_KEY`
- `ELEVENLABS_API_BASE` / `ELEVENLABS_BASE_URL` / `ELEVENLABS_API_KEY`
- `TAVILY_API_BASE` / `TAVILY_BASE_URL` / `TAVILY_API_KEY`
- `SERPAPI_BASE_URL` / `SERPAPI_API_KEY`

These are derived from `AIAPI_URL` and `AIAPI_KEY`, so your API clients will continue to work without changes.

## Backward Compatibility

For backward compatibility, the scripts also set:
- `INFINIPROXY_URL` (derived from `AIAPI_URL`)
- `INFINIPROXY_API_KEY` (derived from `AIAPI_KEY`)

This means **existing code that reads these variables will continue to work** during the migration period.

## Examples

### Local Development

**Before:**
```bash
source set_proxy_env.sh
```

**After:**
```bash
export AIAPI_URL=http://localhost:8000
export AIAPI_KEY=sk-your-key-here
source set_proxy_env.sh
```

### Production Deployment

**Before:**
```bash
export INFINIPROXY_API_KEY=sk-prod-key
source set_proxy_env.sh proxy.production.com
```

**After:**
```bash
export AIAPI_URL=https://proxy.production.com
export AIAPI_KEY=sk-prod-key
source set_proxy_env.sh
```

### Shell Profile

**Before (.bashrc/.zshrc):**
```bash
export INFINIPROXY_API_KEY=sk-your-key
alias proxy-dev='source /path/to/set_proxy_env.sh'
alias proxy-prod='source /path/to/set_proxy_env.sh proxy.production.com'
```

**After (.bashrc/.zshrc):**
```bash
# Development configuration
alias proxy-dev='export AIAPI_URL=http://localhost:8000 && export AIAPI_KEY=sk-dev-key && source /path/to/set_proxy_env.sh'

# Production configuration
alias proxy-prod='export AIAPI_URL=https://proxy.production.com && export AIAPI_KEY=sk-prod-key && source /path/to/set_proxy_env.sh'
```

### CI/CD Pipelines

**Before (GitHub Actions):**
```yaml
- name: Configure Proxy
  run: source set_proxy_env.sh ${{ secrets.PROXY_HOST }}
  env:
    INFINIPROXY_API_KEY: ${{ secrets.PROXY_API_KEY }}
```

**After (GitHub Actions):**
```yaml
- name: Configure Proxy
  run: source set_proxy_env.sh
  env:
    AIAPI_URL: ${{ secrets.AIAPI_URL }}
    AIAPI_KEY: ${{ secrets.AIAPI_KEY }}
```

## Testing Your Migration

After migrating, test your configuration:

```bash
# Set new environment variables
export AIAPI_URL=http://localhost:8000
export AIAPI_KEY=your-api-key-here

# Test Python script
python test_proxy_client_config.py

# Test bash script
source set_proxy_env.sh

# Verify environment variables
env | grep -E "(AIAPI|OPENAI|ANTHROPIC)" | sort
```

Expected output should show:
- `AIAPI_URL` and `AIAPI_KEY` set to your values
- All other API variables properly configured
- No errors or warnings

## Troubleshooting

### Error: "AIAPI_KEY environment variable is not set"

**Cause**: The scripts now require `AIAPI_KEY` to be explicitly set (no default value).

**Fix**:
```bash
export AIAPI_KEY=your-actual-api-key
source set_proxy_env.sh
```

### Variables not persisting across sessions

**Cause**: Environment variables are not saved to shell profile.

**Fix**: Add to `~/.bashrc` or `~/.zshrc`:
```bash
export AIAPI_URL=http://localhost:8000
export AIAPI_KEY=your-api-key
```

### Docker container can't find variables

**Cause**: Environment variables not passed to container.

**Fix**: Update `docker-compose.yml`:
```yaml
services:
  app:
    environment:
      - AIAPI_URL=${AIAPI_URL}
      - AIAPI_KEY=${AIAPI_KEY}
```

## Security Best Practices

1. **Never commit API keys to git**:
   ```bash
   echo ".env" >> .gitignore
   echo "proxy.env" >> .gitignore
   ```

2. **Use different keys for different environments**:
   ```bash
   # Development
   export AIAPI_KEY=sk-dev-...

   # Production (from secrets manager)
   export AIAPI_KEY=$(aws secretsmanager get-secret-value --secret-id prod/aiapi-key --query SecretString --output text)
   ```

3. **Rotate keys regularly**:
   - Update `AIAPI_KEY` value
   - Re-run configuration scripts
   - Test connectivity

4. **Use environment-specific .env files**:
   ```bash
   # .env.development
   AIAPI_URL=http://localhost:8000
   AIAPI_KEY=sk-dev-...

   # .env.production
   AIAPI_URL=https://proxy.production.com
   AIAPI_KEY=sk-prod-...
   ```

## Getting Help

If you encounter issues during migration:

1. Check that `AIAPI_URL` includes the full URL with protocol (http:// or https://)
2. Verify `AIAPI_KEY` is a valid proxy API key (not an upstream provider key)
3. Run `python test_proxy_client_config.py` to verify configuration
4. Check proxy server health: `curl $AIAPI_URL/health`

For additional support, see:
- `PROXY_CLIENT_SETUP.md` - Complete setup documentation
- `README.md` - Project overview and server setup
- `proxy.env.template` - Configuration template with examples
