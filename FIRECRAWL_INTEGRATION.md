# Firecrawl API Integration

This document describes the Firecrawl API integration added to the InfiniProxy service.

## Overview

Firecrawl is a web scraping and crawling API service. This integration adds proxy endpoints that allow authenticated users to access Firecrawl functionality through the InfiniProxy service.

## Configuration

### Environment Variables

Add the following to your `.env` file:

```bash
# Firecrawl API configuration
FIRECRAWL_API_KEY=your-firecrawl-api-key-here
FIRECRAWL_BASE_URL=https://api.firecrawl.dev/v1
```

Get your API key from: https://www.firecrawl.dev/app

### Current Configuration

```
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
FIRECRAWL_BASE_URL=https://api.firecrawl.dev/v1
```

## API Endpoints

All Firecrawl endpoints require authentication via Bearer token (your InfiniProxy API key).

### 1. Scrape Endpoint

**POST** `/v1/firecrawl/scrape`

Scrapes a single URL and returns the content.

**Request Body:**
```json
{
  "url": "https://example.com",
  "formats": ["markdown", "html"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "markdown": "# Example Domain\n\nThis domain is for use...",
    "html": "<html>...</html>",
    "metadata": {
      "title": "Example Domain",
      "language": "en",
      ...
    }
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/firecrawl/scrape \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "formats": ["markdown"]}'
```

### 2. Crawl Endpoint

**POST** `/v1/firecrawl/crawl`

Starts a crawl job for a website.

**Request Body:**
```json
{
  "url": "https://example.com",
  "limit": 10,
  "scrapeOptions": {
    "formats": ["markdown"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "id": "238132ec-7bf0-4c77-b645-6f0d1ddf81c6",
  "url": "https://api.firecrawl.dev/v1/crawl/238132ec-7bf0-4c77-b645-6f0d1ddf81c6"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/firecrawl/crawl \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "limit": 10}'
```

### 3. Crawl Status Endpoint

**GET** `/v1/firecrawl/crawl/status/{job_id}`

Check the status of a crawl job.

**Response:**
```json
{
  "status": "completed",
  "completed": 10,
  "total": 10,
  "creditsUsed": 10,
  "expiresAt": "2024-11-01T00:00:00.000Z",
  "next": "https://api.firecrawl.dev/v1/crawl/status/...",
  "data": [...]
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/v1/firecrawl/crawl/status/238132ec-7bf0-4c77-b645-6f0d1ddf81c6 \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 4. Search Endpoint

**POST** `/v1/firecrawl/search`

Search the web and return results.

**Note**: This endpoint uses Firecrawl API v2 (the search feature is v2-only). Other endpoints use v1.

**Request Body:**
```json
{
  "query": "python web scraping",
  "limit": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "url": "https://example.com",
      "title": "Example Title",
      "description": "Example description..."
    },
    ...
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/v1/firecrawl/search \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "python web scraping", "limit": 5}'
```

## Testing

### Local Testing

1. Start the proxy server:
```bash
python proxy_server.py
```

2. Run the test script:
```bash
export TEST_API_KEY=your-proxy-api-key
export FIRECRAWL_API_KEY=your_firecrawl_api_key_here
python test_firecrawl.py
```

### Test Results

All endpoints tested successfully:
- ✅ Scrape endpoint - Successfully scraped example.com
- ✅ Search endpoint - Successfully searched and returned 5 results
- ✅ Crawl endpoint - Successfully initiated crawl job
- ✅ Status endpoint - Endpoint working correctly

## Usage Tracking

All Firecrawl API calls are tracked in the usage database with:
- Endpoint: `/v1/firecrawl/scrape`, `/v1/firecrawl/crawl`, `/v1/firecrawl/search`
- Model: `firecrawl-scrape`, `firecrawl-crawl`, `firecrawl-search`
- Backend URL: Firecrawl API base URL

## Error Handling

The proxy handles the following error cases:

1. **Missing API Key** (503):
   - Error: "Firecrawl API key not configured"
   - Solution: Set `FIRECRAWL_API_KEY` in environment

2. **Invalid Request** (400):
   - Error: "URL is required" or "Query is required"
   - Solution: Provide required parameters

3. **Firecrawl API Errors** (502):
   - Forwarded from Firecrawl API
   - Check response for specific error details

4. **Authentication Error** (401):
   - Error: "Invalid or inactive API key"
   - Solution: Use a valid InfiniProxy API key

## Implementation Details

### Files Modified

1. **proxy_server.py**:
   - Added 4 new Firecrawl endpoints
   - Updated root endpoint to list Firecrawl endpoints
   - Added proper error handling and logging
   - Integrated with usage tracking system

2. **.env**:
   - Added Firecrawl configuration variables

3. **test_firecrawl.py** (new):
   - Comprehensive test suite for all Firecrawl endpoints
   - Tests authentication, error handling, and functionality

### Code Structure

Each endpoint follows this pattern:
1. Authenticate user via Bearer token
2. Get Firecrawl configuration from environment
3. Validate request parameters
4. Forward request to Firecrawl API
5. Track usage in database
6. Return response to client
7. Handle errors appropriately

## Next Steps

For production deployment:

1. Update `.env` with production Firecrawl API key
2. Ensure SMTP_PASSWORD is configured for email notifications
3. Test all endpoints in production environment
4. Monitor usage and costs through Firecrawl dashboard
5. Set appropriate rate limits if needed

## Resources

- Firecrawl Documentation: https://docs.firecrawl.dev
- Firecrawl Dashboard: https://www.firecrawl.dev/app
- API Reference: https://docs.firecrawl.dev/api-reference/introduction
