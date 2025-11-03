# Deployment Notes - Production Release

## Deployment Information

**Date**: 2025-11-03
**Image**: `harbor.ai.iiis.co:9443/xuw/infiniproxy:latest`
**Digest**: `sha256:35e47a7faa8e90075034db8bd3f64ae752af48c128b5772819093885e1b0cf24`
**Git Commit**: `cba7e11`

## What's Included in This Release

### 1. ElevenLabs WebSocket Fix (cba7e11)
- **Fixed**: WebSocket header parameter for websockets 15.0.1 compatibility
- **Changed**: `extra_headers` → `additional_headers` in both TTS and STT endpoints
- **Status**: TTS WebSocket fully functional, STT requires premium tier
- **Files**: proxy_server.py lines 2323, 2547

### 2. Backward Compatibility for Environment Variables (73baaa3)
- **Added**: Support for both `AIAPI_*` and `INFINIPROXY_*` variable names
- **Behavior**: Scripts accept both conventions with preference for `AIAPI_*`
- **Impact**: Zero breaking changes - existing configurations work without modification
- **Files**: set_proxy_env.sh, set_proxy_env.py, test_proxy_client_config.py

### 3. Environment Variable Migration (1050f40)
- **Changed**: Standardized to `AIAPI_URL` and `AIAPI_KEY` as recommended names
- **Removed**: Hardcoded API key defaults (security improvement)
- **Added**: Clear error messages when API key not set
- **Documentation**: MIGRATION_GUIDE.md, QUICK_START.md

### 4. Proxy Client Configuration Tools (cb94152)
- **Added**: Comprehensive environment configuration scripts
- **Files**: set_proxy_env.sh, set_proxy_env.py, proxy.env.template
- **Features**: Multiple configuration methods (bash, Python, .env files)
- **Documentation**: PROXY_CLIENT_SETUP.md, test_proxy_client_config.py

### 5. Firecrawl Search Fix (b479354)
- **Fixed**: Firecrawl search endpoint to use v2 API
- **Changed**: Explicit v2 endpoint URL
- **Impact**: Search functionality now works correctly
- **Testing**: Multiple successful test queries

## API Endpoints

All endpoints from previous deployments remain functional, plus:

### Fixed Endpoints
- ✅ `/v1/firecrawl/search` - Now uses Firecrawl v2 API (working)
- ✅ `/v1/elevenlabs/text-to-speech/websocket` - WebSocket header fixed (working)
- ⚠️ `/v1/elevenlabs/speech-to-text/websocket` - WebSocket header fixed (requires premium tier)

### All Active Endpoints
- `/health` - Health check
- `/admin/*` - Admin dashboard and API
- `/v1/chat/completions` - OpenAI chat
- `/v1/messages` - Claude messages
- `/v1/firecrawl/*` - Firecrawl (scrape, crawl, search)
- `/v1/elevenlabs/*` - ElevenLabs (TTS, STT, WebSocket)
- `/v1/tavily/*` - Tavily (search, extract)
- `/v1/serpapi/*` - SerpAPI (search variants)

## Environment Variables

### Recommended (New)
```bash
AIAPI_URL=http://localhost:8000
AIAPI_KEY=your-api-key-here
```

### Backward Compatible (Old)
```bash
INFINIPROXY_URL=http://localhost:8000
INFINIPROXY_API_KEY=your-api-key-here
```

**Note**: Both work! Scripts automatically detect which is set and prefer `AIAPI_*` if both exist.

## Configuration Changes Required

**None!** This release is fully backward compatible.

### If Using Old Variables
- No action needed - continue using `INFINIPROXY_*` variables
- Everything works exactly as before

### If Starting Fresh
- Use new `AIAPI_*` variables (recommended)
- See QUICK_START.md for setup instructions

## Testing Performed

### Pre-Deployment
- ✅ 5/5 proxy client configuration tests passed
- ✅ Both variable naming conventions tested
- ✅ Firecrawl search endpoint verified
- ✅ ElevenLabs TTS WebSocket tested (30KB audio received)
- ✅ Health endpoint accessible
- ✅ Docker image builds successfully

### Post-Deployment Validation
```bash
# Test health endpoint
curl http://your-proxy/health

# Test with new variables
export AIAPI_URL=http://your-proxy
export AIAPI_KEY=your-key
source set_proxy_env.sh

# Test with old variables
export INFINIPROXY_URL=http://your-proxy
export INFINIPROXY_API_KEY=your-key
source set_proxy_env.sh
```

## Known Issues

1. **ElevenLabs STT WebSocket**: Requires premium API tier (403 Forbidden)
   - Impact: STT WebSocket unavailable for free tier users
   - Workaround: Use REST API endpoint or upgrade ElevenLabs subscription

2. **ElevenLabs STT REST API**: Quota exceeded on current API key
   - Impact: STT REST endpoint returns quota error
   - Workaround: Upgrade ElevenLabs subscription

## Rollback Plan

If issues arise, rollback to previous image:

```bash
# Get previous image digest from Harbor
docker pull harbor.ai.iiis.co:9443/xuw/infiniproxy:<previous-tag>

# Or rollback Kubernetes deployment
kubectl rollout undo deployment/infiniproxy
```

**Note**: No database schema changes in this release, rollback is safe.

## Documentation Updates

New/updated documentation files:
- ✅ BACKWARD_COMPATIBILITY.md - Variable naming compatibility
- ✅ MIGRATION_GUIDE.md - Migration instructions (optional)
- ✅ QUICK_START.md - Quick reference guide
- ✅ PROXY_CLIENT_SETUP.md - Complete setup guide
- ✅ ELEVENLABS_WEBSOCKET_TESTING.md - WebSocket test results
- ✅ DEPLOYMENT_NOTES.md - This file

## Security Improvements

1. **No Hardcoded Credentials**: API keys must be explicitly set
2. **Clear Error Messages**: Missing credentials are immediately detected
3. **Environment-Based Secrets**: Encourages proper secret management
4. **Backward Compatible**: No security regressions from old setup

## Performance Impact

- No performance degradation expected
- WebSocket fixes improve connection stability
- Firecrawl v2 API may have different response times

## Monitoring Recommendations

Monitor these metrics post-deployment:
- Health endpoint response time
- WebSocket connection success rate
- Firecrawl search request success rate
- Client configuration errors (missing API keys)
- Overall API request success rates

## Next Steps

1. Monitor production logs for any unexpected errors
2. Verify client applications work with both variable conventions
3. Consider updating documentation in client applications to use `AIAPI_*` variables
4. Evaluate ElevenLabs subscription tier for STT requirements

## Support

For issues or questions:
- Check logs: `kubectl logs deployment/infiniproxy`
- Review health: `curl http://your-proxy/health`
- Test configuration: `python test_proxy_client_config.py`
- Reference: PROXY_CLIENT_SETUP.md, BACKWARD_COMPATIBILITY.md

## Git History

```
cba7e11 Fix ElevenLabs WebSocket header parameter for websockets 15.0.1
73baaa3 Add backward compatibility for INFINIPROXY_* environment variables
1050f40 Migrate to AIAPI_URL and AIAPI_KEY environment variables
cb94152 Add comprehensive proxy client configuration tools
b479354 Fix Firecrawl search endpoint to use v2 API
```

**Full changelog**: https://github.com/xuw/infiniproxy/compare/b479354..cba7e11
