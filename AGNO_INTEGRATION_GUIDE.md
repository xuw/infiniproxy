# Agno AI Framework + InfiniProxy Integration Guide

## Overview

**Agno** (formerly Phi Data) is a lightweight framework for building multi-modal AI agents in Python. This guide shows you how to use Agno with InfiniProxy for cost-effective, scalable agent development.

**Compatibility Status**: ✅ **Fully Compatible**

Agno works seamlessly with InfiniProxy through OpenAI-compatible endpoints.

## Quick Start

### Installation

```bash
pip install agno openai
```

### Basic Usage

```python
from agno.agent import Agent
from agno.models.openai.like import OpenAILike

# Configure model to use InfiniProxy
model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-infiniproxy-api-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)

# Create agent
agent = Agent(
    model=model,
    instructions="You are a helpful assistant.",
    markdown=True
)

# Run agent
response = agent.run("What is the capital of France?")
print(response.content)
```

## Configuration Options

### Option 1: Direct Configuration (Recommended)

```python
from agno.models.openai.like import OpenAILike

model = OpenAILike(
    id="gpt-4o-mini",              # Or any OpenAI-compatible model
    api_key="your-api-key",         # InfiniProxy API key
    base_url="https://aiapi.iiis.co:9443/v1"  # InfiniProxy endpoint
)
```

**Pros**:
- ✅ Explicit configuration
- ✅ No environment variables needed
- ✅ Works reliably
- ✅ Easy to debug

### Option 2: Environment Variables

```bash
export OPENAI_API_KEY="your-infiniproxy-api-key"
export OPENAI_BASE_URL="https://aiapi.iiis.co:9443/v1"
```

```python
from agno.models.openai.like import OpenAILike
import os

model = OpenAILike(
    id="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
```

**Note**: Don't use `OpenAIChat` - it doesn't properly override base_url. Always use `OpenAILike`.

## Complete Example: Web Search Agent

```python
from agno.agent import Agent
from agno.models.openai.like import OpenAILike

# Configure model
model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)

# Define a search tool
def search_web(query: str) -> str:
    """Search the web for information"""
    # Your search implementation here
    return f"Search results for: {query}"

# Create agent with tools
agent = Agent(
    model=model,
    tools=[search_web],
    instructions="""
    You are a research assistant with access to web search.
    Use the search_web tool to find current information.
    Always cite your sources.
    """,
    markdown=True
)

# Run agent
response = agent.run("What are the latest AI developments?")
print(response.content)
```

## Agent Features

### 1. Multi-Turn Conversations

```python
agent = Agent(model=model, instructions="You are a helpful assistant.")

# First query
response1 = agent.run("My name is Alice")
print(response1.content)

# Follow-up (agent remembers context)
response2 = agent.run("What's my name?")
print(response2.content)  # Will say "Alice"
```

### 2. Tools and Functions

```python
def get_weather(city: str) -> str:
    """Get weather for a city"""
    return f"Weather in {city}: Sunny, 72°F"

def calculate(expression: str) -> str:
    """Calculate a mathematical expression"""
    return str(eval(expression))

agent = Agent(
    model=model,
    tools=[get_weather, calculate],
    instructions="Use tools to help answer questions."
)

response = agent.run("What's the weather in Paris and what's 25 * 4?")
```

### 3. Knowledge Base Integration

```python
from agno.knowledge.pdf import PDFKnowledgeBase

# Create knowledge base from PDFs
knowledge = PDFKnowledgeBase(
    path="path/to/documents",
    vector_db="pgvector"  # Or other vector DB
)

agent = Agent(
    model=model,
    knowledge=knowledge,
    instructions="Answer questions using the provided documents."
)

response = agent.run("What does the document say about AI?")
```

### 4. Storage and Memory

```python
from agno.storage.postgres import PostgresStorage

# Add persistent storage
storage = PostgresStorage(
    table_name="agent_sessions",
    db_url="postgresql://..."
)

agent = Agent(
    model=model,
    storage=storage,
    instructions="Remember our conversations."
)
```

## Advanced Examples

### Example 1: Data Analysis Agent

```python
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
import pandas as pd

def analyze_data(csv_path: str) -> str:
    """Analyze a CSV file"""
    df = pd.read_csv(csv_path)
    return f"Data summary:\n{df.describe()}"

model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)

agent = Agent(
    model=model,
    tools=[analyze_data],
    instructions="""
    You are a data analyst. When given data files:
    1. Use analyze_data to examine the data
    2. Provide insights and patterns
    3. Suggest next steps
    """
)

response = agent.run("Analyze the sales data in sales.csv")
```

### Example 2: Code Review Agent

```python
from agno.agent import Agent
from agno.models.openai.like import OpenAILike

def read_code_file(file_path: str) -> str:
    """Read a code file"""
    with open(file_path) as f:
        return f.read()

def run_tests(test_command: str) -> str:
    """Run tests"""
    import subprocess
    result = subprocess.run(
        test_command.split(),
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr

model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)

agent = Agent(
    model=model,
    tools=[read_code_file, run_tests],
    instructions="""
    You are a code reviewer. When reviewing code:
    1. Check for bugs and security issues
    2. Suggest improvements
    3. Verify tests pass
    4. Provide actionable feedback
    """
)

response = agent.run("Review the authentication code in auth.py")
```

### Example 3: Multi-Agent System

```python
from agno.agent import Agent
from agno.models.openai.like import OpenAILike

# Configure model
model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)

# Research agent
researcher = Agent(
    model=model,
    name="Researcher",
    instructions="You research topics and gather information."
)

# Writer agent
writer = Agent(
    model=model,
    name="Writer",
    instructions="You write clear, engaging content based on research."
)

# Editor agent
editor = Agent(
    model=model,
    name="Editor",
    instructions="You review and improve written content."
)

# Workflow
research = researcher.run("Research the history of AI")
draft = writer.run(f"Write an article based on: {research.content}")
final = editor.run(f"Edit this article: {draft.content}")

print(final.content)
```

## Model Configuration

### Available Models

InfiniProxy supports OpenAI-compatible models:

```python
# GPT-4o models
model = OpenAILike(id="gpt-4o", ...)           # Most capable
model = OpenAILike(id="gpt-4o-mini", ...)      # Cost-effective

# GPT-4 Turbo
model = OpenAILike(id="gpt-4-turbo", ...)

# GPT-3.5 Turbo
model = OpenAILike(id="gpt-3.5-turbo", ...)
```

### Model Parameters

```python
model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-key",
    base_url="https://aiapi.iiis.co:9443/v1",

    # Optional parameters
    temperature=0.7,        # Control randomness (0-2)
    max_tokens=1000,        # Maximum response length
    top_p=0.9,             # Nucleus sampling
    frequency_penalty=0.0,  # Reduce repetition
    presence_penalty=0.0,   # Encourage topic diversity
)
```

## Best Practices

### 1. Use Clear Instructions

```python
agent = Agent(
    model=model,
    instructions="""
    You are a professional customer support agent.

    Guidelines:
    - Be friendly and helpful
    - Keep responses concise
    - Ask clarifying questions when needed
    - Always maintain a professional tone
    """
)
```

### 2. Optimize Tool Descriptions

```python
def search_database(query: str) -> str:
    """
    Search the customer database.

    Args:
        query: Search query (name, email, or customer ID)

    Returns:
        Customer information or "Not found"
    """
    # Implementation
    pass
```

### 3. Handle Errors Gracefully

```python
try:
    response = agent.run(user_query)
    print(response.content)
except Exception as e:
    print(f"Agent error: {e}")
    # Implement fallback behavior
```

### 4. Monitor Token Usage

```python
response = agent.run("Your query")

# Check usage (if available)
if hasattr(response, 'usage'):
    print(f"Tokens used: {response.usage}")
```

## Testing

Run the test suite:

```bash
python test_agno_proxy.py
```

Expected output:
```
Tests Passed: 4/4
Success Rate: 100.0%
✅ Agno works perfectly with InfiniProxy!
```

## Troubleshooting

### Issue 1: "openai not installed"

**Error**:
```
ImportError: `openai` not installed
```

**Solution**:
```bash
pip install openai -U
```

### Issue 2: "Unknown model error"

**Cause**: Using `OpenAIChat` instead of `OpenAILike`

**Solution**: Always use `OpenAILike`:
```python
# ❌ Wrong - doesn't work
from agno.models.openai import OpenAIChat
model = OpenAIChat(...)

# ✅ Correct - works perfectly
from agno.models.openai.like import OpenAILike
model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)
```

### Issue 3: Connection Errors

**Error**:
```
ConnectionError: Failed to connect
```

**Checklist**:
1. ✅ InfiniProxy URL correct?
2. ✅ API key valid?
3. ✅ Network connectivity?
4. ✅ Firewall allowing HTTPS?

**Test connection**:
```bash
curl -H "Authorization: Bearer your-key" \
  https://aiapi.iiis.co:9443/v1/models
```

### Issue 4: Streaming Not Working

**Note**: There's a known bug in Agno's streaming implementation. Use non-streaming mode:

```python
# ✅ Works
response = agent.run("Your query")

# ⚠️ May have issues
response = agent.run("Your query", stream=True)
```

## Performance Tips

### 1. Reuse Agent Instances

```python
# ✅ Good - reuse agent
agent = Agent(model=model, ...)
for query in queries:
    response = agent.run(query)

# ❌ Bad - creates new agent each time
for query in queries:
    agent = Agent(model=model, ...)
    response = agent.run(query)
```

### 2. Use Appropriate Models

```python
# For simple tasks
model = OpenAILike(id="gpt-3.5-turbo", ...)  # Faster, cheaper

# For complex reasoning
model = OpenAILike(id="gpt-4o", ...)         # More capable
```

### 3. Limit Context When Possible

```python
agent = Agent(
    model=model,
    instructions="Keep responses under 200 words."
)
```

## Integration with InfiniProxy Wrapper

Combine with InfiniProxy wrapper clients for maximum functionality:

```python
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from infiniproxy_clients import TavilyClient, FirecrawlClient

# Configure Agno
model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)

# Create tools using InfiniProxy wrapper clients
tavily = TavilyClient()
firecrawl = FirecrawlClient()

def web_search(query: str) -> str:
    """Search the web"""
    results = tavily.search(query, max_results=5)
    return results['answer']

def scrape_url(url: str) -> str:
    """Scrape a webpage"""
    result = firecrawl.scrape_url(url)
    return result['data']['markdown']

# Create agent with tools
agent = Agent(
    model=model,
    tools=[web_search, scrape_url],
    instructions="You are a research assistant with web access."
)

response = agent.run("Research the latest AI developments and summarize")
```

## Resources

- **Agno Documentation**: https://docs.agno.ai
- **GitHub Repository**: https://github.com/agno-agi/agno
- **InfiniProxy Docs**: See other guides in this repository
- **Test Suite**: `test_agno_proxy.py`

## Summary

✅ **Fully Compatible**: Agno works seamlessly with InfiniProxy
✅ **Easy Setup**: Just configure `base_url` parameter
✅ **All Features**: Tools, knowledge, storage all work
✅ **Production Ready**: Tested and validated

**Recommended Configuration**:
```python
from agno.models.openai.like import OpenAILike

model = OpenAILike(
    id="gpt-4o-mini",
    api_key="your-infiniproxy-key",
    base_url="https://aiapi.iiis.co:9443/v1"
)
```

This provides the best compatibility and reliability with InfiniProxy.
