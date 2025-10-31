# SerpAPI Proxy Integration

This document describes the SerpAPI integration in the InfiniProxy server.

## Overview

The proxy server now supports proxying requests to SerpAPI for various Google search services:
- Google Search (organic results)
- Google Images
- Google News
- Google Shopping
- Google Maps/Local Search

## Configuration

Add the following environment variable to configure SerpAPI integration:

```bash
# Required
SERPAPI_API_KEY=your_serpapi_api_key_here

# Optional (defaults shown)
SERPAPI_BASE_URL=https://serpapi.com/search
```

Get your API key from: https://serpapi.com/manage-api-key

## Available Endpoints

### 1. Google Search

**Endpoint:** `GET /v1/serpapi/search`

**Authentication:** Bearer token (user API key)

**Query Parameters:**
- `q` (required): Search query
- `location` (optional): Location for the search (e.g., "Austin, Texas")
- `gl` (optional): Country code (e.g., "us", "uk", "cn")
- `hl` (optional): Language code (e.g., "en", "zh-cn")
- `num` (optional): Number of results (1-100, default: 10)

**Response:** JSON with search results including:
```json
{
  "search_metadata": {
    "id": "search_id",
    "status": "Success",
    "created_at": "2025-01-31 12:00:00 UTC",
    "processed_at": "2025-01-31 12:00:01 UTC",
    "total_time_taken": 0.5
  },
  "search_parameters": {
    "engine": "google",
    "q": "your search query",
    "location_requested": "Austin, Texas",
    "device": "desktop"
  },
  "organic_results": [
    {
      "position": 1,
      "title": "Result Title",
      "link": "https://example.com",
      "displayed_link": "example.com",
      "snippet": "Result description...",
      "date": "Jan 30, 2025"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/v1/serpapi/search?q=artificial+intelligence&num=10&gl=us&hl=en" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/v1/serpapi/search"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
params = {
    "q": "artificial intelligence",
    "num": 10,
    "gl": "us",
    "hl": "en"
}

response = requests.get(url, headers=headers, params=params)
results = response.json()
print(results)
```

### 2. Google Images

**Endpoint:** `GET /v1/serpapi/images`

**Authentication:** Bearer token (user API key)

**Query Parameters:**
- `q` (required): Image search query
- `gl` (optional): Country code
- `hl` (optional): Language code
- `num` (optional): Number of results (default: 10)

**Response:** JSON with image results including thumbnails, original images, and metadata

**Example:**
```bash
curl "http://localhost:8000/v1/serpapi/images?q=sunset+beach&num=20" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/v1/serpapi/images"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
params = {
    "q": "sunset beach",
    "num": 20
}

response = requests.get(url, headers=headers, params=params)
images = response.json()

for img in images.get("images_results", []):
    print(f"Title: {img['title']}")
    print(f"Thumbnail: {img['thumbnail']}")
    print(f"Original: {img['original']}")
```

### 3. Google News

**Endpoint:** `GET /v1/serpapi/news`

**Authentication:** Bearer token (user API key)

**Query Parameters:**
- `q` (required): News search query
- `location` (optional): Location for the news
- `gl` (optional): Country code
- `hl` (optional): Language code
- `num` (optional): Number of results (default: 10)

**Response:** JSON with news articles including:
```json
{
  "news_results": [
    {
      "position": 1,
      "title": "Article Title",
      "link": "https://news-site.com/article",
      "source": "News Source",
      "date": "2 hours ago",
      "snippet": "Article preview...",
      "thumbnail": "https://..."
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/v1/serpapi/news?q=technology+updates&num=20" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/v1/serpapi/news"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
params = {
    "q": "technology updates",
    "num": 20
}

response = requests.get(url, headers=headers, params=params)
news = response.json()

for article in news.get("news_results", []):
    print(f"{article['title']} - {article['source']}")
    print(f"{article['date']}: {article['snippet']}\n")
```

### 4. Google Shopping

**Endpoint:** `GET /v1/serpapi/shopping`

**Authentication:** Bearer token (user API key)

**Query Parameters:**
- `q` (required): Product search query
- `location` (optional): Location for shopping results
- `gl` (optional): Country code
- `hl` (optional): Language code
- `num` (optional): Number of results (default: 10)

**Response:** JSON with shopping results including:
```json
{
  "shopping_results": [
    {
      "position": 1,
      "title": "Product Name",
      "link": "https://store.com/product",
      "product_link": "https://...",
      "product_id": "12345",
      "price": "$99.99",
      "extracted_price": 99.99,
      "rating": 4.5,
      "reviews": 1234,
      "thumbnail": "https://...",
      "delivery": "Free delivery"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/v1/serpapi/shopping?q=laptop&num=20&gl=us" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/v1/serpapi/shopping"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
params = {
    "q": "laptop",
    "num": 20,
    "gl": "us"
}

response = requests.get(url, headers=headers, params=params)
products = response.json()

for product in products.get("shopping_results", []):
    print(f"{product['title']} - {product['price']}")
    print(f"Rating: {product.get('rating', 'N/A')} ({product.get('reviews', 0)} reviews)\n")
```

### 5. Google Maps / Local Search

**Endpoint:** `GET /v1/serpapi/maps`

**Authentication:** Bearer token (user API key)

**Query Parameters:**
- `q` (required): Location/business search query
- `location` (optional): Location center point
- `gl` (optional): Country code
- `hl` (optional): Language code
- `num` (optional): Number of results (default: 10)

**Response:** JSON with local business results including:
```json
{
  "local_results": [
    {
      "position": 1,
      "title": "Business Name",
      "rating": 4.7,
      "reviews": 523,
      "type": "Restaurant",
      "address": "123 Main St, City, State 12345",
      "phone": "+1 234-567-8900",
      "hours": "Open ⋅ Closes 10 PM",
      "thumbnail": "https://..."
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/v1/serpapi/maps?q=coffee+shops&location=San+Francisco,CA" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/v1/serpapi/maps"
headers = {"Authorization": "Bearer YOUR_API_KEY"}
params = {
    "q": "coffee shops",
    "location": "San Francisco, CA"
}

response = requests.get(url, headers=headers, params=params)
places = response.json()

for place in places.get("local_results", []):
    print(f"{place['title']} - {place.get('rating', 'N/A')}⭐")
    print(f"{place.get('address', 'N/A')}")
    print(f"Phone: {place.get('phone', 'N/A')}\n")
```

## Common Parameters

All endpoints support these common parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `q` | string | Search query (required) | `artificial intelligence` |
| `location` | string | Geographic location | `Austin, Texas` |
| `gl` | string | Country code (2 letters) | `us`, `uk`, `cn` |
| `hl` | string | Language code | `en`, `zh-cn`, `es` |
| `num` | integer | Number of results (1-100) | `10`, `20`, `50` |

## Country Codes (gl parameter)

Common country codes:
- `us` - United States
- `uk` - United Kingdom
- `cn` - China
- `jp` - Japan
- `de` - Germany
- `fr` - France
- `in` - India
- `au` - Australia
- `ca` - Canada

See full list: https://serpapi.com/google-countries

## Language Codes (hl parameter)

Common language codes:
- `en` - English
- `zh-cn` - Chinese (Simplified)
- `zh-tw` - Chinese (Traditional)
- `es` - Spanish
- `fr` - French
- `de` - German
- `ja` - Japanese
- `ko` - Korean

See full list: https://serpapi.com/google-languages

## Usage Tracking

All SerpAPI calls are tracked in the usage database with:
- **Input tokens:** Query length (for tracking search complexity)
- **Output tokens:** 0 (output is structured data)
- **Model names:**
  - `serpapi-search` - Google Search
  - `serpapi-images` - Google Images
  - `serpapi-news` - Google News
  - `serpapi-shopping` - Google Shopping
  - `serpapi-maps` - Google Maps

## Error Handling

All endpoints return appropriate HTTP status codes:
- `400` - Bad request (missing required parameters like `q`)
- `401` - Unauthorized (invalid user API key)
- `503` - Service unavailable (SerpAPI key not configured)
- `500` - Internal server error

Error responses include detailed error messages in JSON format:
```json
{
  "detail": "Error message describing the issue"
}
```

## Rate Limiting

Rate limiting is handled by SerpAPI. The proxy passes through all rate limit responses.

Your SerpAPI plan determines:
- Searches per month
- Concurrent requests
- API features available

Check your plan at: https://serpapi.com/pricing

## Architecture

The proxy acts as a middleware between clients and SerpAPI:

```
Client → InfiniProxy → SerpAPI
         ↓
    User Authentication
    Usage Tracking
    Logging
    Query Parameter Forwarding
```

**Benefits:**
1. Unified API key management
2. Usage tracking and analytics per user
3. Access control per user
4. Centralized logging and monitoring
5. Cost tracking per user/team
6. Query parameter validation

## Security Notes

1. The SerpAPI key is stored server-side and never exposed to clients
2. Clients authenticate with their proxy API keys
3. All requests are logged for audit purposes
4. Query parameters are validated before forwarding
5. API keys should be stored securely in environment variables or secrets management

## Testing

### Quick Test - Google Search
```bash
export API_KEY="your_proxy_api_key"

curl "http://localhost:8000/v1/serpapi/search?q=test+query&num=5" \
  -H "Authorization: Bearer $API_KEY"
```

### Quick Test - Google Images
```bash
curl "http://localhost:8000/v1/serpapi/images?q=sunset&num=5" \
  -H "Authorization: Bearer $API_KEY"
```

### Quick Test - Google News
```bash
curl "http://localhost:8000/v1/serpapi/news?q=technology&num=5" \
  -H "Authorization: Bearer $API_KEY"
```

### Quick Test - Google Shopping
```bash
curl "http://localhost:8000/v1/serpapi/shopping?q=laptop&num=5" \
  -H "Authorization: Bearer $API_KEY"
```

### Quick Test - Google Maps
```bash
curl "http://localhost:8000/v1/serpapi/maps?q=restaurants&location=New+York" \
  -H "Authorization: Bearer $API_KEY"
```

### Comprehensive Test Suite

Use the provided test script:
```bash
export TEST_API_KEY="your_proxy_api_key"
python test_serpapi.py
```

## Use Cases

### 1. Market Research
Use Google Search and News to track industry trends and competitor mentions.

### 2. Product Discovery
Use Google Shopping to find products, compare prices, and track availability.

### 3. Content Discovery
Use Google Images to find relevant images for content creation.

### 4. Local Business Intelligence
Use Google Maps to research local competitors and market density.

### 5. News Monitoring
Use Google News to track brand mentions and industry developments.

## Troubleshooting

### "SerpAPI API key not configured"
Ensure `SERPAPI_API_KEY` environment variable is set.

### Empty Results
- Check if your query is too specific
- Try different location/language parameters
- Verify your SerpAPI plan includes the search type

### Rate Limit Errors
- Check your SerpAPI dashboard for quota usage
- Upgrade your plan if needed
- Implement client-side rate limiting

### Slow Response Times
- SerpAPI typically responds in 1-3 seconds
- Network latency may add additional time
- Consider caching frequent queries

## Best Practices

1. **Query Optimization**:
   - Use specific, targeted queries
   - Include relevant keywords
   - Use location parameters for local results

2. **Result Pagination**:
   - Start with smaller `num` values
   - Implement pagination if needed
   - Cache results to reduce API calls

3. **Parameter Usage**:
   - Always specify `gl` and `hl` for consistent results
   - Use `location` for location-specific searches
   - Validate user input before making requests

4. **Error Handling**:
   - Implement retry logic for transient failures
   - Handle rate limits gracefully
   - Log errors for debugging

5. **Cost Management**:
   - Cache frequent queries
   - Set reasonable `num` limits
   - Monitor usage per user/team
   - Alert on unusual usage patterns

## Advanced Features

### Custom Parameters

You can pass additional SerpAPI parameters through query strings:
```bash
curl "http://localhost:8000/v1/serpapi/search?q=test&start=10&filter=1" \
  -H "Authorization: Bearer $API_KEY"
```

### Response Caching

Consider implementing response caching for:
- Identical queries within time window
- Popular/trending searches
- Static reference data

Example cache key: `serpapi:{endpoint}:{query_hash}:{params_hash}`

### Analytics and Monitoring

Track these metrics:
- Queries per user/team
- Popular search terms
- Response times
- Error rates
- Cost per query type

## API Reference Links

- SerpAPI Documentation: https://serpapi.com/docs
- Google Search: https://serpapi.com/search-api
- Google Images: https://serpapi.com/images-results
- Google News: https://serpapi.com/news-results
- Google Shopping: https://serpapi.com/shopping-results
- Google Maps: https://serpapi.com/google-maps-api

## Future Enhancements

Possible improvements:
1. Add more search engines (Bing, Baidu, Yandex)
2. Add specialized searches (Scholar, Patents, Jobs)
3. Implement response caching layer
4. Add webhook support for async searches
5. Implement search result filtering/transformation
6. Add batch search capabilities
7. Implement search analytics dashboard
8. Add A/B testing support for queries
