"""
Datadog LLM Observability Integration

This module initializes Datadog APM and LLM Observability for tracking:
- OpenAI API calls and costs
- LangChain/LangGraph agent executions
- Custom metrics and traces
- Performance and error monitoring
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global flag to track initialization
_datadog_initialized = False


def init_datadog(settings=None) -> bool:
    """
    Initialize Datadog LLM Observability and APM tracing.

    Args:
        settings: Optional Settings object to read configuration from

    Returns:
        bool: True if successfully initialized, False otherwise
    """
    global _datadog_initialized

    if _datadog_initialized:
        logger.info("Datadog already initialized")
        return True

    # Check if Datadog is enabled
    # Try settings first, fall back to os.getenv for flexibility
    dd_api_key = None
    if settings and hasattr(settings, 'DD_API_KEY'):
        dd_api_key = settings.DD_API_KEY
    else:
        dd_api_key = os.getenv("DD_API_KEY")

    if not dd_api_key:
        logger.warning("⚠️ DD_API_KEY not set. Datadog monitoring disabled.")
        logger.warning("   Set DD_API_KEY environment variable to enable monitoring.")
        return False

    try:
        from ddtrace import tracer, patch_all
        from ddtrace.llmobs import LLMObs

        # Patch all supported libraries (OpenAI, LangChain, etc.)
        patch_all()
        logger.info("Datadog auto-instrumentation enabled")

        # Get configuration values from settings or env vars
        dd_site = getattr(settings, 'DD_SITE', None) or os.getenv("DD_SITE", "datadoghq.com")
        dd_env = getattr(settings, 'DD_ENV', None) or os.getenv("DD_ENV", "production")
        dd_service = getattr(settings, 'DD_SERVICE', None) or os.getenv("DD_SERVICE", "stylistai-backend")
        dd_ml_app = getattr(settings, 'DD_LLMOBS_ML_APP', None) or os.getenv("DD_LLMOBS_ML_APP", "stylistai")
        dd_agent_host = getattr(settings, 'DD_AGENT_HOST', None) or os.getenv("DD_AGENT_HOST", "localhost")
        dd_agent_port = getattr(settings, 'DD_TRACE_AGENT_PORT', None) or os.getenv("DD_TRACE_AGENT_PORT", "8126")

        # Enable LLM Observability
        LLMObs.enable(
            ml_app=dd_ml_app,
            site=dd_site,
            api_key=dd_api_key,
            env=dd_env,
            service=dd_service,
        )
        logger.info("Datadog LLM Observability enabled")

        # Log configuration
        logger.info(f"📊 Datadog Configuration:")
        logger.info(f"   Service: {dd_service}")
        logger.info(f"   Environment: {dd_env}")
        logger.info(f"   ML App: {dd_ml_app}")
        logger.info(f"   Site: {dd_site}")

        _datadog_initialized = True
        return True

    except ImportError as e:
        logger.error(f"❌ Failed to import ddtrace: {str(e)}")
        logger.error("   Install with: pip install ddtrace")
        return False

    except Exception as e:
        logger.error(f"❌ Failed to initialize Datadog: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def shutdown_datadog():
    """Shutdown Datadog on application exit"""
    global _datadog_initialized

    if not _datadog_initialized:
        return

    try:
        from ddtrace.llmobs import LLMObs

        LLMObs.disable()
        logger.info("Datadog LLM Observability disabled")

        _datadog_initialized = False

    except Exception as e:
        logger.error(f"Error shutting down Datadog: {str(e)}")


def is_datadog_enabled() -> bool:
    """Check if Datadog is enabled and initialized"""
    return _datadog_initialized


def get_tracer():
    """
    Get the Datadog tracer instance.

    Returns:
        Tracer instance or None if Datadog is not initialized
    """
    if not _datadog_initialized:
        return None

    try:
        from ddtrace import tracer
        return tracer
    except ImportError:
        return None
