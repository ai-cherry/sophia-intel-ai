"""
Sentry configuration for SOPHIA Intel error tracking
"""

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging

def init_sentry():
    """
    Initialize Sentry for error tracking and performance monitoring
    """
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("PYTHON_ENV", "development")
    
    if sentry_dsn:
        # Configure logging integration
        logging_integration = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )
        
        # Initialize Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(auto_enabling_integrations=False),
                logging_integration,
            ],
            # Performance monitoring
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            # Error sampling
            sample_rate=1.0,
            # Release tracking
            release=f"sophia-intel@{os.getenv('VERSION', '1.0.0')}",
            # Additional options
            attach_stacktrace=True,
            send_default_pii=False,  # Don't send personally identifiable information
        )
        
        logging.info(f"Sentry initialized for environment: {environment}")
        return True
    else:
        logging.warning("SENTRY_DSN not configured, error tracking disabled")
        return False

def capture_exception(error: Exception, extra_data: dict = None):
    """
    Capture an exception with additional context
    """
    with sentry_sdk.configure_scope() as scope:
        if extra_data:
            for key, value in extra_data.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)

def capture_message(message: str, level: str = "info", extra_data: dict = None):
    """
    Capture a custom message
    """
    with sentry_sdk.configure_scope() as scope:
        if extra_data:
            for key, value in extra_data.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)

def set_user_context(user_id: str, email: str = None):
    """
    Set user context for error tracking
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_user({
            "id": user_id,
            "email": email
        })

def set_tag(key: str, value: str):
    """
    Set a tag for filtering errors
    """
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag(key, value)

