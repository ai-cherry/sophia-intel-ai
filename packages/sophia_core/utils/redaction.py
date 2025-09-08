"""Redaction utilities for PII and sensitive data."""

import logging
import re
from re import Pattern
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class RedactionPatterns:
    """Common patterns for sensitive data redaction."""

    # API Keys and tokens
    API_KEY = re.compile(
        r'(api[_-]?key|apikey|api_secret|access[_-]?token)["\']?\s*[:=]\s*["\']?([A-Za-z0-9\-_]{20,})["\']?',
        re.IGNORECASE,
    )
    BEARER_TOKEN = re.compile(r"Bearer\s+([A-Za-z0-9\-_\.]+)", re.IGNORECASE)

    # AWS
    AWS_ACCESS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
    AWS_SECRET_KEY = re.compile(
        r'aws[_-]?secret[_-]?access[_-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9/+=]{40})["\']?',
        re.IGNORECASE,
    )

    # Emails
    EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    # Phone numbers (US format)
    PHONE_US = re.compile(r"\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b")

    # Credit cards
    CREDIT_CARD = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

    # SSN
    SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

    # IP Addresses
    IPV4 = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
    IPV6 = re.compile(r"(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|::)")

    # URLs with credentials
    URL_CREDS = re.compile(r"(https?|ftp)://[^:]+:[^@]+@[^\s]+")

    # Database connection strings
    DB_CONN = re.compile(r"(postgresql|mysql|mongodb|redis)://[^:]+:[^@]+@[^\s]+")

    # JWT tokens
    JWT = re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")


class Redactor:
    """Redacts sensitive information from text and data structures."""

    def __init__(
        self,
        patterns: Optional[Dict[str, Pattern]] = None,
        custom_patterns: Optional[Dict[str, Pattern]] = None,
        replacement: str = "[REDACTED]",
    ):
        """Initialize redactor.

        Args:
            patterns: Dictionary of pattern name to regex pattern
            custom_patterns: Additional custom patterns to use
            replacement: String to replace sensitive data with
        """
        self.replacement = replacement

        # Use default patterns if none provided
        if patterns is None:
            patterns = {
                "api_key": RedactionPatterns.API_KEY,
                "bearer_token": RedactionPatterns.BEARER_TOKEN,
                "aws_access_key": RedactionPatterns.AWS_ACCESS_KEY,
                "aws_secret_key": RedactionPatterns.AWS_SECRET_KEY,
                "email": RedactionPatterns.EMAIL,
                "phone_us": RedactionPatterns.PHONE_US,
                "credit_card": RedactionPatterns.CREDIT_CARD,
                "ssn": RedactionPatterns.SSN,
                "ipv4": RedactionPatterns.IPV4,
                "url_creds": RedactionPatterns.URL_CREDS,
                "db_conn": RedactionPatterns.DB_CONN,
                "jwt": RedactionPatterns.JWT,
            }

        self.patterns = patterns

        # Add custom patterns
        if custom_patterns:
            self.patterns.update(custom_patterns)

    def redact_text(self, text: str) -> str:
        """Redact sensitive information from text.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        if not text:
            return text

        redacted = text

        for name, pattern in self.patterns.items():
            try:
                # Handle patterns with groups
                if pattern.groups > 0:
                    redacted = pattern.sub(
                        lambda m: m.group(0).replace(m.group(pattern.groups), self.replacement),
                        redacted,
                    )
                else:
                    redacted = pattern.sub(self.replacement, redacted)
            except Exception as e:
                logger.warning(f"Failed to apply redaction pattern {name}: {e}")

        return redacted

    def redact_dict(
        self, data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Redact sensitive information from dictionary.

        Args:
            data: Dictionary to redact
            sensitive_keys: Additional keys to redact entirely

        Returns:
            Redacted dictionary
        """
        if not data:
            return data

        # Default sensitive keys
        if sensitive_keys is None:
            sensitive_keys = [
                "password",
                "passwd",
                "pwd",
                "secret",
                "token",
                "key",
                "api_key",
                "apikey",
                "auth",
                "authorization",
                "credential",
            ]

        redacted = {}

        for key, value in data.items():
            # Check if key is sensitive
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                redacted[key] = self.replacement
            elif isinstance(value, str):
                redacted[key] = self.redact_text(value)
            elif isinstance(value, dict):
                redacted[key] = self.redact_dict(value, sensitive_keys)
            elif isinstance(value, list):
                redacted[key] = self.redact_list(value, sensitive_keys)
            else:
                redacted[key] = value

        return redacted

    def redact_list(self, data: List[Any], sensitive_keys: Optional[List[str]] = None) -> List[Any]:
        """Redact sensitive information from list.

        Args:
            data: List to redact
            sensitive_keys: Keys to consider sensitive in nested dicts

        Returns:
            Redacted list
        """
        if not data:
            return data

        redacted = []

        for item in data:
            if isinstance(item, str):
                redacted.append(self.redact_text(item))
            elif isinstance(item, dict):
                redacted.append(self.redact_dict(item, sensitive_keys))
            elif isinstance(item, list):
                redacted.append(self.redact_list(item, sensitive_keys))
            else:
                redacted.append(item)

        return redacted

    def redact_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Redact sensitive HTTP headers.

        Args:
            headers: HTTP headers dictionary

        Returns:
            Redacted headers
        """
        sensitive_headers = [
            "authorization",
            "x-api-key",
            "x-auth-token",
            "cookie",
            "set-cookie",
            "x-csrf-token",
        ]

        redacted = {}

        for key, value in headers.items():
            if key.lower() in sensitive_headers:
                redacted[key] = self.replacement
            else:
                redacted[key] = self.redact_text(value)

        return redacted


# Global redactor instance
default_redactor = Redactor()


def redact(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """Convenience function to redact data using default redactor.

    Args:
        data: Data to redact (string, dict, or list)

    Returns:
        Redacted data
    """
    if isinstance(data, str):
        return default_redactor.redact_text(data)
    elif isinstance(data, dict):
        return default_redactor.redact_dict(data)
    elif isinstance(data, list):
        return default_redactor.redact_list(data)
    else:
        return data
