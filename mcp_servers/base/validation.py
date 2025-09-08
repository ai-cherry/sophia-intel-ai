from shared.validation.validators import (
    validate_max_tokens,
    validate_temperature,
    validate_url,
)

"\nInput validation utilities for MCP servers\n"
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .error_handling import MCPValidationError


@dataclass
class ValidationRule:
    """Validation rule definition"""

    field: str
    required: bool = False
    type_check: type | None = None
    min_value: int | float | None = None
    max_value: int | float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    choices: list[Any] | None = None
    custom_validator: Callable[[Any], bool] | None = None
    error_message: str | None = None


class MCPToolValidator:
    """Validator for MCP tool inputs"""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.rules: list[ValidationRule] = []

    def add_rule(self, rule: ValidationRule) -> "MCPToolValidator":
        """Add validation rule"""
        self.rules.append(rule)
        return self

    def require_field(
        self, field: str, field_type: type = str, **kwargs
    ) -> "MCPToolValidator":
        """Add required field rule"""
        rule = ValidationRule(
            field=field, required=True, type_check=field_type, **kwargs
        )
        return self.add_rule(rule)

    def optional_field(
        self, field: str, field_type: type = str, **kwargs
    ) -> "MCPToolValidator":
        """Add optional field rule"""
        rule = ValidationRule(
            field=field, required=False, type_check=field_type, **kwargs
        )
        return self.add_rule(rule)

    def validate(self, data: dict[str, Any]) -> None:
        """Validate data against all rules"""
        if not isinstance(data, dict):
            raise MCPValidationError(
                f"Tool '{self.tool_name}' expects a dictionary of arguments",
                field="arguments",
            )
        for rule in self.rules:
            self._validate_field(data, rule)

    def _validate_field(self, data: dict[str, Any], rule: ValidationRule) -> None:
        """Validate a single field"""
        field_name = rule.field
        if rule.required and field_name not in data:
            raise MCPValidationError(
                rule.error_message or f"Required field '{field_name}' is missing",
                field=field_name,
            )
        if field_name not in data:
            return
        value = data[field_name]
        if rule.type_check and (not isinstance(value, rule.type_check)):
            raise MCPValidationError(
                rule.error_message
                or f"Field '{field_name}' must be of type {rule.type_check.__name__}",
                field=field_name,
                value=value,
            )
        if (
            rule.min_value is not None
            and isinstance(value, int | float)
            and (value < rule.min_value)
        ):
            raise MCPValidationError(
                rule.error_message
                or f"Field '{field_name}' must be >= {rule.min_value}",
                field=field_name,
                value=value,
            )
        if (
            rule.max_value is not None
            and isinstance(value, int | float)
            and (value > rule.max_value)
        ):
            raise MCPValidationError(
                rule.error_message
                or f"Field '{field_name}' must be <= {rule.max_value}",
                field=field_name,
                value=value,
            )
        if (
            rule.min_length is not None
            and isinstance(value, str)
            and (len(value) < rule.min_length)
        ):
            raise MCPValidationError(
                rule.error_message
                or f"Field '{field_name}' must be at least {rule.min_length} characters",
                field=field_name,
                value=value,
            )
        if (
            rule.max_length is not None
            and isinstance(value, str)
            and (len(value) > rule.max_length)
        ):
            raise MCPValidationError(
                rule.error_message
                or f"Field '{field_name}' must be at most {rule.max_length} characters",
                field=field_name,
                value=value,
            )
        if rule.pattern and isinstance(value, str):
            if not re.match(rule.pattern, value):
                raise MCPValidationError(
                    rule.error_message
                    or f"Field '{field_name}' does not match required pattern",
                    field=field_name,
                    value=value,
                )
        if rule.choices and value not in rule.choices:
            raise MCPValidationError(
                rule.error_message
                or f"Field '{field_name}' must be one of: {', '.join(map(str, rule.choices))}",
                field=field_name,
                value=value,
            )
        if rule.custom_validator:
            try:
                if not rule.custom_validator(value):
                    raise MCPValidationError(
                        rule.error_message
                        or f"Field '{field_name}' failed custom validation",
                        field=field_name,
                        value=value,
                    )
            except Exception as e:
                if isinstance(e, MCPValidationError):
                    raise
                raise MCPValidationError(
                    f"Custom validation error for field '{field_name}': {str(e)}",
                    field=field_name,
                    value=value,
                )


class CommonValidators:
    """Collection of common validators for MCP tools"""

    @staticmethod
    def search_query_validator(tool_name: str) -> MCPToolValidator:
        """Validator for search query tools"""
        return (
            MCPToolValidator(tool_name)
            .require_field("query", str, min_length=1, max_length=1000)
            .optional_field("max_results", int, min_value=1, max_value=100)
            .optional_field("language", str, max_length=10)
        )

    @staticmethod
    def ai_chat_validator(tool_name: str) -> MCPToolValidator:
        """Validator for AI chat tools"""
        return (
            MCPToolValidator(tool_name)
            .require_field("prompt", str, min_length=1, max_length=10000)
            .optional_field("model", str, max_length=100)
            .optional_field("temperature", float, custom_validator=validate_temperature)
            .optional_field("max_tokens", int, custom_validator=validate_max_tokens)
            .optional_field("system_prompt", str, max_length=5000)
        )

    @staticmethod
    def code_analysis_validator(tool_name: str) -> MCPToolValidator:
        """Validator for code analysis tools"""
        return (
            MCPToolValidator(tool_name)
            .require_field("code", str, min_length=1, max_length=50000)
            .optional_field("language", str, max_length=20)
            .optional_field(
                "analysis_type",
                str,
                choices=["review", "refactor", "explain", "debug", "complete"],
            )
        )

    @staticmethod
    def api_request_validator(tool_name: str) -> MCPToolValidator:
        """Validator for API request tools"""
        return (
            MCPToolValidator(tool_name)
            .require_field(
                "endpoint",
                str,
                min_length=1,
                max_length=500,
                custom_validator=validate_url,
            )
            .optional_field(
                "method", str, choices=["GET", "POST", "PUT", "DELETE", "PATCH"]
            )
            .optional_field("headers", dict)
            .optional_field("timeout", int, min_value=1, max_value=300)
        )

    @staticmethod
    def file_operation_validator(tool_name: str) -> MCPToolValidator:
        """Validator for file operation tools"""
        return (
            MCPToolValidator(tool_name)
            .require_field("path", str, min_length=1, max_length=500)
            .optional_field("encoding", str, choices=["utf-8", "ascii", "latin-1"])
            .optional_field("create_dirs", bool)
        )

    @staticmethod
    def repository_validator(tool_name: str) -> MCPToolValidator:
        """Validator for repository operation tools"""
        return (
            MCPToolValidator(tool_name)
            .require_field("owner", str, min_length=1, max_length=100)
            .require_field("repo", str, min_length=1, max_length=100)
            .optional_field("ref", str, max_length=100)
            .optional_field("path", str, max_length=500)
        )


"""
validation.py - Syntax errors fixed
This file had severe syntax errors and was replaced with a minimal valid structure.
"""
