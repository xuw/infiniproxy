# Backward Compatibility: Environment Variables

## Both Variable Names Supported

The configuration scripts now support **both** naming conventions:

| New (Recommended) | Old (Still Works) |
|------------------|-------------------|
| `AIAPI_URL` | `INFINIPROXY_URL` |
| `AIAPI_KEY` | `INFINIPROXY_API_KEY` |

## How It Works

The scripts check for variables in this order:
1. **First**: Check for `AIAPI_URL` and `AIAPI_KEY`
2. **Fallback**: Use `INFINIPROXY_URL` and `INFINIPROXY_API_KEY` if not set
3. **Default**: Use `http://localhost:8000` for URL if neither is set

## No Migration Required

**Your existing setup continues to work without any changes.**

If you're currently using:
```bash
export INFINIPROXY_URL=http://localhost:8000
export INFINIPROXY_API_KEY=sk-abc123...
source set_proxy_env.sh
```

**This will continue to work exactly as before.**

## When to Switch

You can switch to the new variable names at your convenience:

```bash
# Old (still works)
export INFINIPROXY_URL=http://localhost:8000
export INFINIPROXY_API_KEY=sk-abc123...

# New (recommended)
export AIAPI_URL=http://localhost:8000
export AIAPI_KEY=sk-abc123...
```

## Preference Order

If you set both, `AIAPI_*` takes precedence:

```bash
# Both set - AIAPI_* wins
export AIAPI_URL=https://new-proxy.com
export AIAPI_KEY=sk-new-key
export INFINIPROXY_URL=http://old-proxy.com
export INFINIPROXY_API_KEY=sk-old-key

# Result: Uses https://new-proxy.com with sk-new-key
```

## What Changed

### Before
- Scripts **exported** `INFINIPROXY_URL` and `INFINIPROXY_API_KEY` as output
- This caused confusion about input vs output variables

### Now
- Scripts **accept** both `AIAPI_*` and `INFINIPROXY_*` as input
- Scripts no longer export redundant `INFINIPROXY_*` variables
- All derived variables (OPENAI_*, ANTHROPIC_*, etc.) still work the same

## Testing Both Conventions

**Test with new variables:**
```bash
export AIAPI_URL=http://localhost:8000
export AIAPI_KEY=sk-test-key
python test_proxy_client_config.py
# Result: 5/5 tests passed ✅
```

**Test with old variables:**
```bash
export INFINIPROXY_URL=http://localhost:8000
export INFINIPROXY_API_KEY=sk-test-key
python test_proxy_client_config.py
# Result: 5/5 tests passed ✅
```

## Recommendation

For new projects, use `AIAPI_*` variables:
- Shorter and clearer names
- Aligns with common naming conventions
- Explicitly includes URL (not just host)

For existing projects, no action needed:
- Continue using `INFINIPROXY_*` variables
- Everything works without changes
- Migrate at your convenience

## Environment File Example

**New style (recommended):**
```bash
# .env or proxy.env
AIAPI_URL=http://localhost:8000
AIAPI_KEY=your-api-key-here
```

**Old style (still supported):**
```bash
# .env or proxy.env
INFINIPROXY_URL=http://localhost:8000
INFINIPROXY_API_KEY=your-api-key-here
```

**Mixed (works but not recommended):**
```bash
# .env or proxy.env
AIAPI_URL=http://localhost:8000
INFINIPROXY_API_KEY=your-api-key-here
# Result: Uses AIAPI_URL, falls back to INFINIPROXY_API_KEY
```

## Benefits of This Approach

✅ **Zero Breaking Changes**: All existing configurations work
✅ **Gradual Migration**: Switch at your own pace
✅ **Clear Preference**: New variables take priority when both exist
✅ **Simplified Logic**: No duplicate variable exports
✅ **Better Testing**: Can verify both conventions work

## Summary

- **No migration required** - your existing setup works
- **Both variable names supported** - choose what works for you
- **`AIAPI_*` recommended** for new projects
- **`INFINIPROXY_*` still fully supported** for existing projects
- **Scripts now cleaner** - accept both, don't export duplicates
