# Tavily API Proxy Integration

This document describes the Tavily API integration in the InfiniProxy server.

## Overview

The proxy server now supports proxying requests to Tavily AI for:
- **AI-powered Search** - Advanced search with LLM-generated answers
- **Content Extraction** - Web scraping optimized for LLMs

Tavily is designed specifically for AI agents and LLMs, providing high-quality search results and clean content extraction.

## Configuration

Add the following environment variable to configure Tavily integration:

```bash
# Required
TAVILY_API_KEY=your_tavily_api_key_here
```

Get your API key from: https://app.tavily.com/

## Available Endpoints

### 1. Tavily Search

**Endpoint:** `POST /v1/tavily/search`

**Authentication:** Bearer token (user API key)

**Request Body:**
```json
{
  "query": "search query",
  "search_depth": "basic",
  "topic": "general",
  "max_results": 5,
  "include_answer": true,
  "include_images": false
}
```

**Required Parameters:**
- `query` (string): The search term to execute

**Optional Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auto_parameters` | boolean | false | Automatically configure search settings |
| `topic` | string | general | Category: `general`, `news`, or `finance` |
| `search_depth` | string | basic | `basic` (1 credit) or `advanced` (2 credits) |
| `chunks_per_source` | integer | 3 | Content snippets per source (1-3, advanced only) |
| `max_results` | integer | 5 | Maximum results (0-20) |
| `time_range` | string | null | `day`, `week`, `month`, `year` (or `d`, `w`, `m`, `y`) |
| `start_date` | string | null | Results after date (YYYY-MM-DD) |
| `end_date` | string | null | Results before date (YYYY-MM-DD) |
| `include_answer` | boolean/string | false | `false`, `true`/`basic`, or `advanced` |
| `include_raw_content` | boolean/string | false | `false`, `true`/`markdown`, or `text` |
| `include_images` | boolean | false | Include image search results |
| `include_image_descriptions` | boolean | false | Add descriptive text for images |
| `include_favicon` | boolean | false | Include favicon URLs |
| `include_domains` | array | [] | Whitelist domains (max 300) |
| `exclude_domains` | array | [] | Blacklist domains (max 150) |
| `country` | string | null | Boost results from specific country |

**Response:**
```json
{
  "query": "artificial intelligence",
  "answer": "LLM-generated answer to the query...",
  "images": [
    {
      "url": "https://example.com/image.jpg",
      "description": "Image description"
    }
  ],
  "results": [
    {
      "title": "Result Title",
      "url": "https://example.com",
      "content": "Brief description...",
      "score": 0.95,
      "raw_content": "Full content in markdown...",
      "favicon": "https://example.com/favicon.ico"
    }
  ],
  "response_time": 1.23,
  "request_id": "uuid-string"
}
```

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/v1/tavily/search" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest AI developments 2024",
    "search_depth": "advanced",
    "max_results": 10,
    "include_answer": true,
    "include_images": true,
    "time_range": "month"
  }'
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/v1/tavily/search"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
payload = {
    "query": "latest AI developments 2024",
    "search_depth": "advanced",
    "max_results": 10,
    "include_answer": True,
    "include_images": True,
    "time_range": "month"
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

print(f"Answer: {result['answer']}")
print(f"\nResults:")
for r in result['results']:
    print(f"- {r['title']} (score: {r['score']})")
    print(f"  {r['url']}")
```

### 2. Tavily Extract

**Endpoint:** `POST /v1/tavily/extract`

**Authentication:** Bearer token (user API key)

**Request Body:**
```json
{
  "urls": ["https://example.com", "https://another.com"],
  "extract_depth": "basic",
  "include_images": false,
  "format": "markdown"
}
```

**Required Parameters:**
- `urls` (string or array): The URL(s) to extract content from (max 20)

**Optional Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_images` | boolean | false | Include images extracted from URLs |
| `include_favicon` | boolean | false | Include favicon URL |
| `extract_depth` | string | basic | `basic` or `advanced` (more data, higher cost) |
| `format` | string | markdown | `markdown` or `text` |
| `timeout` | number | 10/30 | Max wait time (1.0-60.0 seconds) |

**Response:**
```json
{
  "results": [
    {
      "url": "https://example.com",
      "raw_content": "Extracted content in markdown format...",
      "images": ["https://example.com/img1.jpg"],
      "favicon": "https://example.com/favicon.ico"
    }
  ],
  "failed_results": [
    {
      "url": "https://failed.com",
      "error": "Timeout"
    }
  ],
  "response_time": 2.34,
  "request_id": "uuid-string"
}
```

**Example (cURL):**
```bash
curl -X POST "http://localhost:8000/v1/tavily/extract" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://docs.python.org/3/tutorial/",
      "https://www.python.org/about/"
    ],
    "extract_depth": "advanced",
    "include_images": true,
    "format": "markdown"
  }'
```

**Example (Python):**
```python
import requests

url = "http://localhost:8000/v1/tavily/extract"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
payload = {
    "urls": [
        "https://docs.python.org/3/tutorial/",
        "https://www.python.org/about/"
    ],
    "extract_depth": "advanced",
    "include_images": True,
    "format": "markdown"
}

response = requests.post(url, headers=headers, json=payload)
result = response.json()

print(f"Successful extractions: {len(result['results'])}")
print(f"Failed extractions: {len(result['failed_results'])}")

for r in result['results']:
    print(f"\nURL: {r['url']}")
    print(f"Content length: {len(r['raw_content'])} characters")
```

## Search Topics

### General Search (default)
- Broad web search across all content types
- Best for: Research, general information, product discovery

### News Search
- Focused on recent news articles
- Best for: Current events, breaking news, trending topics

### Finance Search
- Specialized financial information
- Best for: Market data, company information, financial news

**Example:**
```json
{
  "query": "NVIDIA stock performance",
  "topic": "finance",
  "time_range": "week"
}
```

## Search Depth Comparison

### Basic Search (1 credit)
- Fast results (1-2 seconds)
- Essential information
- Up to 3 chunks per source
- Best for: Quick lookups, simple queries

### Advanced Search (2 credits)
- Comprehensive results (2-4 seconds)
- More detailed content
- Up to 3 chunks per source (configurable)
- Best for: In-depth research, complex queries

## Extract Depth Comparison

### Basic Extraction (1 credit per 5 URLs)
- Standard extraction
- Timeout: 10 seconds default
- Best for: Simple pages, quick extraction

### Advanced Extraction (2 credits per 5 URLs)
- Deep extraction with tables and embedded content
- Timeout: 30 seconds default
- Higher success rate
- Best for: Complex pages, comprehensive data

## Time Filtering

Filter search results by recency:

```json
{
  "query": "AI breakthroughs",
  "time_range": "month"
}
```

Or use specific date ranges:

```json
{
  "query": "AI research",
  "start_date": "2024-01-01",
  "end_date": "2024-06-30"
}
```

## Domain Filtering

### Include Specific Domains
```json
{
  "query": "machine learning tutorials",
  "include_domains": ["github.com", "arxiv.org", "medium.com"]
}
```

### Exclude Specific Domains
```json
{
  "query": "Python programming",
  "exclude_domains": ["stackoverflow.com", "reddit.com"]
}
```

## LLM-Generated Answers

Get AI-generated answers based on search results:

### Basic Answer
```json
{
  "query": "What is quantum computing?",
  "include_answer": true
}
```

### Advanced Answer
```json
{
  "query": "Explain quantum computing applications",
  "include_answer": "advanced"
}
```

## Raw Content Extraction

Get full page content in search results:

### Markdown Format
```json
{
  "query": "React best practices",
  "include_raw_content": "markdown",
  "search_depth": "advanced"
}
```

### Plain Text Format
```json
{
  "query": "React best practices",
  "include_raw_content": "text",
  "search_depth": "advanced"
}
```

## Image Search

Include relevant images in search results:

```json
{
  "query": "Golden Gate Bridge",
  "include_images": true,
  "include_image_descriptions": true
}
```

## Country-Specific Search

Boost results from a specific country (general topic only):

```json
{
  "query": "local restaurants",
  "country": "US",
  "topic": "general"
}
```

## Usage Tracking

All Tavily calls are tracked in the usage database:

**Search Endpoint:**
- **Model name:** `tavily-search`
- **Input tokens:** Query word count
- **Output tokens:** 0 (structured data)

**Extract Endpoint:**
- **Model name:** `tavily-extract`
- **Input tokens:** Number of URLs
- **Output tokens:** 0 (structured data)

## Error Handling

All endpoints return appropriate HTTP status codes:

| Code | Meaning |
|------|---------|
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid user API key) |
| 429 | Rate limit exceeded |
| 432 | Plan usage limit exceeded |
| 433 | Pay-as-you-go limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable (Tavily key not configured) |

Error responses include detailed messages:
```json
{
  "detail": "Error message describing the issue"
}
```

## Rate Limiting

Rate limiting is handled by Tavily API. The proxy passes through all rate limit responses.

Your Tavily plan determines:
- Requests per month
- Credits per request (based on search_depth/extract_depth)
- Available features

Check your plan at: https://app.tavily.com/

## Architecture

The proxy acts as a middleware:

```
Client → InfiniProxy → Tavily AI
         ↓
    User Authentication
    Usage Tracking
    Logging
    Parameter Forwarding
```

**Benefits:**
1. Unified API key management
2. Usage tracking per user
3. Access control per user
4. Centralized logging
5. Cost tracking
6. Parameter validation

## Security Notes

1. Tavily API key stored server-side only
2. Clients authenticate with proxy API keys
3. All requests logged for audit
4. Request body validation
5. Secure environment variable storage

## Use Cases

### 1. AI-Powered Research
```python
# Get comprehensive research with AI summary
response = requests.post(
    "http://localhost:8000/v1/tavily/search",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "query": "Impact of AI on healthcare",
        "search_depth": "advanced",
        "include_answer": "advanced",
        "max_results": 20,
        "include_raw_content": "markdown"
    }
)
```

### 2. News Monitoring
```python
# Track recent news on a topic
response = requests.post(
    "http://localhost:8000/v1/tavily/search",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "query": "artificial intelligence regulation",
        "topic": "news",
        "time_range": "week",
        "max_results": 10
    }
)
```

### 3. Content Extraction for RAG
```python
# Extract content for RAG systems
urls = [
    "https://docs.langchain.com/docs/use-cases/qa-docs",
    "https://python.langchain.com/docs/tutorials/"
]

response = requests.post(
    "http://localhost:8000/v1/tavily/extract",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "urls": urls,
        "extract_depth": "advanced",
        "format": "markdown"
    }
)

# Use extracted content for embeddings
for result in response.json()['results']:
    content = result['raw_content']
    # Process content for RAG system
```

### 4. Academic Research
```python
# Search academic sources
response = requests.post(
    "http://localhost:8000/v1/tavily/search",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "query": "quantum entanglement applications",
        "include_domains": ["arxiv.org", "nature.com", "science.org"],
        "search_depth": "advanced",
        "max_results": 15
    }
)
```

### 5. Competitive Intelligence
```python
# Monitor competitor websites
competitor_urls = [
    "https://competitor1.com/about",
    "https://competitor2.com/products",
    "https://competitor3.com/blog"
]

response = requests.post(
    "http://localhost:8000/v1/tavily/extract",
    headers={"Authorization": f"Bearer {api_key}"},
    json={
        "urls": competitor_urls,
        "extract_depth": "advanced",
        "include_images": True
    }
)
```

## Best Practices

### Search Optimization

1. **Use Appropriate Depth:**
   - `basic` for quick lookups
   - `advanced` for comprehensive research

2. **Filter Smartly:**
   - Use domain filters to focus results
   - Apply time filters for recent information
   - Specify topic for better relevance

3. **Answer Generation:**
   - Request answers only when needed
   - Use `advanced` answer for complex queries

4. **Result Quantity:**
   - Start with fewer results (5-10)
   - Increase only if needed
   - More results = higher cost

### Extract Optimization

1. **Batch Processing:**
   - Extract multiple URLs in one request
   - Maximum 20 URLs per request
   - Better performance than individual requests

2. **Choose Right Depth:**
   - `basic` for simple text pages
   - `advanced` for complex pages with tables

3. **Format Selection:**
   - `markdown` preserves structure
   - `text` for plain content (may be slower)

4. **Timeout Management:**
   - Set appropriate timeouts
   - Default: 10s (basic), 30s (advanced)
   - Increase for slow-loading pages

### Cost Management

1. **Monitor Credits:**
   - Basic search: 1 credit
   - Advanced search: 2 credits
   - Extract basic: 1 credit per 5 URLs
   - Extract advanced: 2 credits per 5 URLs

2. **Cache Results:**
   - Implement client-side caching
   - Reuse search results when possible
   - Cache extracted content

3. **Optimize Queries:**
   - Be specific to get better results
   - Use filters to reduce irrelevant results
   - Avoid redundant searches

## Testing

### Quick Test - Search
```bash
export API_KEY="your_proxy_api_key"

curl -X POST "http://localhost:8000/v1/tavily/search" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "max_results": 3}'
```

### Quick Test - Extract
```bash
curl -X POST "http://localhost:8000/v1/tavily/extract" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'
```

### Comprehensive Test Suite

Use the provided test script:
```bash
export TEST_API_KEY="your_proxy_api_key"
python test_tavily.py
```

## Troubleshooting

### "Tavily API key not configured"
Ensure `TAVILY_API_KEY` environment variable is set.

### 429 Rate Limit Exceeded
- Check your Tavily dashboard for quota
- Implement client-side rate limiting
- Upgrade your plan if needed

### 432/433 Usage Limit Exceeded
- Monthly limit reached
- Check plan limits at app.tavily.com
- Upgrade plan or wait for reset

### Empty or Poor Results
- Refine query to be more specific
- Try different search depth
- Use domain filters
- Check spelling and grammar

### Extraction Failures
- Increase timeout for slow pages
- Try advanced extraction depth
- Check if URL is accessible
- Some sites may block scraping

## API Reference Links

- Tavily Documentation: https://docs.tavily.com/
- Tavily Search API: https://docs.tavily.com/documentation/api-reference/endpoint/search
- Tavily Extract API: https://docs.tavily.com/documentation/api-reference/endpoint/extract
- Tavily Dashboard: https://app.tavily.com/
- Tavily Pricing: https://tavily.com/pricing

## Future Enhancements

Possible improvements:
1. Add response caching layer
2. Implement batch search operations
3. Add webhook support for async operations
4. Implement search result aggregation
5. Add custom scoring/ranking
6. Integrate with vector databases for RAG
7. Add analytics dashboard
8. Support for streaming responses
