# Datadog LLM Observability Implementation Guide

This guide covers integrating Datadog LLM Observability into StylistAI to monitor OpenAI API calls, LangChain/LangGraph agents, costs, and performance.

## 📊 Overview

### What Datadog LLM Observability Provides:

1. **Cost Tracking**
   - Token usage per request
   - Cost per user/session
   - Daily/monthly spend analytics
   - Model-wise cost breakdown

2. **Performance Monitoring**
   - API call latency
   - Time to first token
   - Total response time
   - Bottleneck identification

3. **Quality & Errors**
   - API errors and retries
   - Rate limit tracking
   - Failed requests
   - Error patterns

4. **Usage Analytics**
   - Requests per endpoint
   - Popular queries
   - User engagement metrics
   - Agent tool usage

5. **LangChain/LangGraph Tracing**
   - Agent decision flow
   - Tool calls visualization
   - Chain execution paths
   - State transitions

---

## 🚀 Implementation Steps

### Step 1: Install Datadog SDK

```bash
# Activate virtual environment
source venv/bin/activate

# Install Datadog APM
pip install ddtrace

# Install LLM Observability (built into ddtrace)
pip install ddtrace[openai]

# Update requirements.txt
pip freeze | grep ddtrace >> requirements.txt
```

### Step 2: Set Up Environment Variables

Add to your `.env` file:

```bash
# Datadog Configuration
DD_API_KEY=your_datadog_api_key
DD_SITE=datadoghq.com  # or datadoghq.eu for EU
DD_SERVICE=stylistai-backend
DD_ENV=production  # or development, staging
DD_VERSION=1.0.0

# Enable LLM Observability
DD_LLMOBS_ENABLED=true
DD_LLMOBS_ML_APP=stylistai

# Enable OpenAI integration
DD_TRACE_OPENAI_ENABLED=true

# Optional: APM settings
DD_TRACE_ENABLED=true
DD_LOGS_INJECTION=true
```

### Step 3: Initialize Datadog in Your Application

Create `app/core/datadog.py`:

```python
"""
Datadog LLM Observability Integration
"""

import os
from ddtrace import tracer
from ddtrace.llmobs import LLMObs
import logging

logger = logging.getLogger(__name__)


def init_datadog():
    """Initialize Datadog LLM Observability"""

    # Check if Datadog is enabled
    if not os.getenv("DD_API_KEY"):
        logger.warning("DD_API_KEY not set. Datadog monitoring disabled.")
        return

    try:
        # Enable LLM Observability
        LLMObs.enable(
            ml_app=os.getenv("DD_LLMOBS_ML_APP", "stylistai"),
            site=os.getenv("DD_SITE", "datadoghq.com"),
            api_key=os.getenv("DD_API_KEY"),
            env=os.getenv("DD_ENV", "production"),
        )

        # Configure tracer
        tracer.configure(
            hostname=os.getenv("DD_AGENT_HOST", "localhost"),
            port=int(os.getenv("DD_TRACE_AGENT_PORT", 8126)),
        )

        logger.info("✅ Datadog LLM Observability initialized")

    except Exception as e:
        logger.error(f"❌ Failed to initialize Datadog: {str(e)}")


def shutdown_datadog():
    """Shutdown Datadog on application exit"""
    try:
        LLMObs.disable()
        logger.info("Datadog LLM Observability disabled")
    except Exception as e:
        logger.error(f"Error shutting down Datadog: {str(e)}")
```

### Step 4: Update `app/main.py`

```python
from fastapi import FastAPI
from app.core.datadog import init_datadog, shutdown_datadog

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    # ... existing startup code ...

    # Initialize Datadog
    init_datadog()
    logger.info("Datadog monitoring initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    # Shutdown Datadog
    shutdown_datadog()
    logger.info("Application shutdown complete")
```

### Step 5: Instrument LangChain/LangGraph Agents

Update your agent files to add tracing:

**For `app/services/onboarding_agent_autonomous.py`:**

```python
from ddtrace import tracer
from ddtrace.llmobs import LLMObs

async def run_autonomous_onboarding(
    user_id: str,
    user_message: Optional[str],
    conversation_history: List[dict]
):
    """Run autonomous onboarding with Datadog tracing"""

    # Start LLM Observability span
    with tracer.trace("onboarding.agent", service="stylistai-onboarding") as span:
        span.set_tag("user_id", user_id)
        span.set_tag("message_count", len(conversation_history))

        try:
            # Create workflow
            workflow = create_onboarding_workflow()

            # Run the workflow
            with tracer.trace("onboarding.workflow.invoke") as workflow_span:
                result = await workflow.ainvoke(
                    {
                        "messages": messages,
                        "user_id": user_id,
                        "collected_data": {}
                    },
                    config={"recursion_limit": 20}
                )

            # Track completion
            is_complete = result.get("is_complete", False)
            span.set_tag("onboarding.complete", is_complete)

            # Track collected fields
            collected_data = result.get("collected_data", {})
            span.set_tag("fields_collected", len(collected_data))

            return {
                "response": ai_response,
                "is_complete": is_complete,
                "collected_data": collected_data
            }

        except Exception as e:
            span.set_tag("error", True)
            span.set_tag("error.message", str(e))
            logger.error(f"Onboarding error: {str(e)}")
            raise
```

**For `app/services/langgraph_agent.py`:**

```python
from ddtrace import tracer

async def run_styling_agent(user_id: str, query: str, conversation_history: List):
    """Run styling agent with Datadog tracing"""

    with tracer.trace("styling.agent", service="stylistai-styling") as span:
        span.set_tag("user_id", user_id)
        span.set_tag("query", query[:100])  # First 100 chars

        try:
            # Get user preferences
            with tracer.trace("styling.get_preferences") as pref_span:
                user_prefs = UserService.get_user_preferences(user_id)
                pref_span.set_tag("has_preferences", user_prefs is not None)

            # Get weather
            with tracer.trace("styling.get_weather") as weather_span:
                weather = await get_weather_for_location(...)
                weather_span.set_tag("temperature", weather.get("temperature"))

            # Run LangGraph workflow
            with tracer.trace("styling.workflow.invoke") as workflow_span:
                result = await workflow.ainvoke(state)

                # Track tool calls
                if "tool_calls" in result:
                    workflow_span.set_tag("tools_called", len(result["tool_calls"]))
                    workflow_span.set_tag("tool_names", [t["name"] for t in result["tool_calls"]])

            span.set_tag("response_length", len(result.get("response", "")))
            return result

        except Exception as e:
            span.set_tag("error", True)
            span.set_tag("error.message", str(e))
            raise
```

### Step 6: Track Custom Metrics

Add custom metrics for business logic:

```python
from ddtrace import tracer
from ddtrace.llmobs import LLMObs

# Track wardrobe search
with tracer.trace("wardrobe.search") as span:
    results = await ImageService.search_similar_outfits(
        query=query,
        user_id=user_id,
        n_results=5
    )

    span.set_tag("results_count", len(results))
    span.set_tag("top_similarity", results[0]["similarity"] if results else 0)
    span.set_metric("wardrobe.items_found", len(results))

# Track photo uploads
with tracer.trace("wardrobe.upload") as span:
    span.set_tag("photo_count", len(files))
    span.set_metric("wardrobe.photos_uploaded", len(files))

    # Process images...

    span.set_tag("embeddings_generated", successful_count)
```

### Step 7: Add Request-Level Tracking

Update API endpoints to track user sessions:

```python
from fastapi import Request
from ddtrace import tracer

@router.post("/styling/query")
async def query_styling_agent(
    query: QueryRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Styling query endpoint with Datadog tracking"""

    with tracer.trace("api.styling.query", service="stylistai-api") as span:
        span.set_tag("user_id", current_user["uid"])
        span.set_tag("endpoint", "/styling/query")

        # Track request metadata
        span.set_tag("user_agent", request.headers.get("user-agent", ""))
        span.set_tag("query_length", len(query.query))

        try:
            result = await run_styling_agent(...)

            # Track response metadata
            span.set_tag("recommendations_count", len(result.get("recommendations", [])))
            span.set_metric("styling.query_success", 1)

            return result

        except Exception as e:
            span.set_tag("error", True)
            span.set_metric("styling.query_failure", 1)
            raise
```

---

## 🔧 Configuration Files

### Update `app/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Datadog settings
    DD_API_KEY: Optional[str] = None
    DD_SITE: str = "datadoghq.com"
    DD_SERVICE: str = "stylistai-backend"
    DD_ENV: str = "production"
    DD_VERSION: str = "1.0.0"
    DD_LLMOBS_ENABLED: bool = True
    DD_LLMOBS_ML_APP: str = "stylistai"
    DD_TRACE_OPENAI_ENABLED: bool = True
    DD_TRACE_ENABLED: bool = True
```

---

## 🐳 Docker Setup (Optional)

If using Docker, update `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - DD_API_KEY=${DD_API_KEY}
      - DD_SITE=${DD_SITE}
      - DD_SERVICE=stylistai-backend
      - DD_ENV=${DD_ENV}
      - DD_VERSION=1.0.0
      - DD_LLMOBS_ENABLED=true
      - DD_LLMOBS_ML_APP=stylistai
      - DD_TRACE_OPENAI_ENABLED=true
      - DD_AGENT_HOST=datadog-agent
    labels:
      com.datadoghq.tags.service: "stylistai-backend"
      com.datadoghq.tags.env: "${DD_ENV}"
      com.datadoghq.tags.version: "1.0.0"

  datadog-agent:
    image: gcr.io/datadoghq/agent:7
    environment:
      - DD_API_KEY=${DD_API_KEY}
      - DD_SITE=${DD_SITE}
      - DD_APM_ENABLED=true
      - DD_APM_NON_LOCAL_TRAFFIC=true
      - DD_DOGSTATSD_NON_LOCAL_TRAFFIC=true
      - DD_LOGS_ENABLED=true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc/:/host/proc/:ro
      - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
    ports:
      - "8125:8125/udp"  # DogStatsD
      - "8126:8126/tcp"  # APM
```

---

## 🚀 Running with Datadog

### Local Development:

```bash
# Method 1: Without Datadog Agent (direct to Datadog API)
export DD_API_KEY=your_api_key
export DD_SITE=datadoghq.com
export DD_ENV=development
python -m uvicorn app.main:app --reload

# Method 2: With ddtrace wrapper
ddtrace-run uvicorn app.main:app --reload
```

### Production (GCP VM):

```bash
# Install Datadog Agent on VM
DD_API_KEY=your_api_key DD_SITE="datadoghq.com" bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script_agent7.sh)"

# Start your application
ddtrace-run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📊 Datadog Dashboard Setup

### Key Metrics to Monitor:

1. **LLM Costs**
   - `llm.tokens.prompt` - Input tokens
   - `llm.tokens.completion` - Output tokens
   - `llm.cost` - Total cost per request

2. **Performance**
   - `llm.latency` - API response time
   - `llm.time_to_first_token` - Time to start streaming
   - `trace.duration` - End-to-end request time

3. **Usage**
   - `llm.requests` - Total API calls
   - `llm.errors` - Failed requests
   - `styling.queries` - User queries count

4. **Agent Metrics**
   - `agent.tool_calls` - Tool usage frequency
   - `wardrobe.searches` - Vector DB queries
   - `onboarding.completion_rate` - Success rate

### Create Dashboards:

1. Go to Datadog → Dashboards → New Dashboard
2. Add widgets for:
   - LLM cost per day/week/month
   - Average latency per endpoint
   - Error rates
   - Most expensive queries
   - Tool call distribution
   - User engagement metrics

---

## 🧪 Testing

### Test the Integration:

```python
# Test script: test_datadog.py
import asyncio
from app.services.onboarding_agent_autonomous import run_autonomous_onboarding

async def test_datadog_tracing():
    """Test Datadog tracing with a sample request"""

    result = await run_autonomous_onboarding(
        user_id="test_user_123",
        user_message="I like minimalist style",
        conversation_history=[]
    )

    print("✅ Request completed - Check Datadog for traces!")
    print(f"Response: {result['response'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_datadog_tracing())
```

Run and check Datadog APM → Traces for your requests.

---

## 📈 Expected Results

After implementation, you'll see in Datadog:

1. **APM Traces** showing full request flow:
   ```
   API Request → Auth → Get Preferences → Get Weather →
   LangGraph Agent → Tool Calls → OpenAI API → Response
   ```

2. **LLM Observability** dashboard with:
   - Token usage trends
   - Cost per user/session
   - Model performance comparison
   - Error patterns

3. **Custom Metrics**:
   - Wardrobe searches per user
   - Photo upload success rate
   - Onboarding completion rate

---

## 🔐 Security Notes

- ⚠️ Never commit `DD_API_KEY` to git
- ⚠️ Use environment variables for all secrets
- ⚠️ Limit PII in span tags (hash user IDs if needed)
- ⚠️ Review Datadog's data retention policies

---

## 📚 Resources

- [Datadog LLM Observability Docs](https://docs.datadoghq.com/llm_observability/)
- [Python APM Setup](https://docs.datadoghq.com/tracing/setup_overview/setup/python/)
- [LangChain Integration](https://docs.datadoghq.com/llm_observability/setup/langchain/)
- [OpenAI Integration](https://docs.datadoghq.com/integrations/openai/)

---

## 🎯 Next Steps

1. Get Datadog API key from [app.datadoghq.com](https://app.datadoghq.com)
2. Install ddtrace: `pip install ddtrace[openai]`
3. Add environment variables to `.env`
4. Initialize Datadog in `app/main.py`
5. Add tracing to agent files
6. Deploy and monitor!
