"""
Response Handler for Model Outputs
Handles JSON extraction, validation, and fallback strategies.
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ResponseHandler:
    """Robust handler for model responses with multiple extraction strategies."""

    @staticmethod
    def extract_json(text: str) -> dict[str, Any] | None:
        """
        Extract JSON from various text formats.
        
        Tries multiple strategies:
        1. Direct JSON parsing
        2. Extract from markdown code blocks
        3. Find JSON-like structures with regex
        4. Clean and retry
        5. Build structured fallback
        """
        if not text or not text.strip():
            logger.warning("Empty response received")
            return None

        # Strategy 1: Try direct JSON parsing
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code blocks
        json_from_markdown = ResponseHandler._extract_from_markdown(text)
        if json_from_markdown:
            return json_from_markdown

        # Strategy 3: Find JSON-like structure with regex
        json_from_regex = ResponseHandler._extract_with_regex(text)
        if json_from_regex:
            return json_from_regex

        # Strategy 4: Clean common issues and retry
        cleaned_json = ResponseHandler._clean_and_parse(text)
        if cleaned_json:
            return cleaned_json

        # Strategy 5: Build structured fallback from text
        return ResponseHandler._build_fallback_structure(text)

    @staticmethod
    def _extract_from_markdown(text: str) -> dict[str, Any] | None:
        """Extract JSON from markdown code blocks."""
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'`([^`]+)`'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Try to parse each match as JSON
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        return None

    @staticmethod
    def _extract_with_regex(text: str) -> dict[str, Any] | None:
        """Extract JSON-like structures using regex."""
        # Look for object-like structures
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text)

        for match in matches:
            try:
                # Attempt to parse each match
                parsed = json.loads(match)
                # Validate it has expected structure
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _clean_and_parse(text: str) -> dict[str, Any] | None:
        """Clean common JSON issues and retry parsing."""
        # Remove common prefixes/suffixes
        cleaners = [
            (r'^.*?(?={)', ''),  # Remove everything before first {
            (r'}[^}]*$', '}'),   # Remove everything after last }
            (r',\s*}', '}'),     # Remove trailing commas
            (r',\s*]', ']'),     # Remove trailing commas in arrays
            (r'(\w+):', r'"\1":'),  # Quote unquoted keys
            (r':\s*\'([^\']*?)\'', r': "\1"'),  # Convert single to double quotes
            (r'None', 'null'),  # Python None to JSON null
            (r'True', 'true'),  # Python True to JSON true
            (r'False', 'false'), # Python False to JSON false
        ]

        cleaned = text
        for pattern, replacement in cleaners:
            cleaned = re.sub(pattern, replacement, cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _build_fallback_structure(text: str) -> dict[str, Any]:
        """Build a structured response from unstructured text."""
        # Try to extract key-value pairs
        kv_pattern = r'(\w+):\s*([^\n,]+)'
        matches = re.findall(kv_pattern, text)

        if matches:
            result = {}
            for key, value in matches:
                # Clean and convert values
                value = value.strip()
                if value.lower() in ['true', 'false']:
                    result[key] = value.lower() == 'true'
                elif value.lower() == 'none' or value.lower() == 'null':
                    result[key] = None
                elif value.isdigit():
                    result[key] = int(value)
                elif ResponseHandler._is_float(value):
                    result[key] = float(value)
                else:
                    result[key] = value.strip('"\'')
            return result

        # Ultimate fallback - wrap text in structure
        return {
            "response": text,
            "parsed": False,
            "fallback": True
        }

    @staticmethod
    def _is_float(value: str) -> bool:
        """Check if string is a float."""
        try:
            float(value)
            return '.' in value
        except ValueError:
            return False

    @staticmethod
    def validate_response(response: dict[str, Any], required_fields: list[str]) -> bool:
        """Validate that response contains required fields."""
        if not isinstance(response, dict):
            return False

        for field in required_fields:
            if field not in response:
                logger.warning(f"Missing required field: {field}")
                return False

        return True

    @staticmethod
    def ensure_structure(
        response: str | dict,
        template: dict[str, Any],
        required_fields: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Ensure response matches expected structure.
        
        Args:
            response: Raw response (string or dict)
            template: Expected structure template
            required_fields: List of required field names
            
        Returns:
            Structured response matching template
        """
        # Extract JSON if string
        if isinstance(response, str):
            response = ResponseHandler.extract_json(response)

        if not response:
            logger.warning("Failed to extract JSON, using template")
            return template

        # Merge with template to ensure all fields exist
        result = template.copy()
        result.update(response)

        # Validate required fields
        if required_fields:
            if not ResponseHandler.validate_response(result, required_fields):
                logger.warning("Validation failed, adding missing fields")
                for field in required_fields:
                    if field not in result:
                        result[field] = template.get(field)

        return result

    @staticmethod
    def extract_code_blocks(text: str) -> list[str]:
        """Extract code blocks from text."""
        code_blocks = []

        # Match fenced code blocks
        fenced_pattern = r'```(?:\w+)?\s*(.*?)\s*```'
        fenced_matches = re.findall(fenced_pattern, text, re.DOTALL)
        code_blocks.extend(fenced_matches)

        # Match indented code blocks (4 spaces or tab)
        lines = text.split('\n')
        current_block = []
        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                current_block.append(line[4:] if line.startswith('    ') else line[1:])
            elif current_block:
                code_blocks.append('\n'.join(current_block))
                current_block = []

        if current_block:
            code_blocks.append('\n'.join(current_block))

        return code_blocks


class ModelResponseValidator:
    """Validator for specific model response types."""

    @staticmethod
    def validate_critic_response(response: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize critic response."""
        template = {
            "verdict": "revise",
            "findings": {
                "security": [],
                "data_integrity": [],
                "logic_correctness": [],
                "performance": [],
                "usability": [],
                "maintainability": []
            },
            "must_fix": [],
            "nice_to_have": [],
            "confidence_score": 0.7
        }

        result = ResponseHandler.ensure_structure(
            response,
            template,
            ["verdict", "findings"]
        )

        # Ensure verdict is valid
        if result["verdict"] not in ["pass", "revise"]:
            result["verdict"] = "revise"

        return result

    @staticmethod
    def validate_judge_response(response: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize judge response."""
        template = {
            "decision": "reject",
            "confidence_score": 0.5,
            "runner_instructions": [],
            "merge_strategy": None,
            "risk_assessment": "medium"
        }

        result = ResponseHandler.ensure_structure(
            response,
            template,
            ["decision"]
        )

        # Ensure decision is valid
        if result["decision"] not in ["accept", "merge", "reject"]:
            result["decision"] = "reject"

        # Add runner instructions if accepting
        if result["decision"] in ["accept", "merge"] and not result["runner_instructions"]:
            result["runner_instructions"] = ["Proceed with implementation"]

        return result

    @staticmethod
    def validate_generator_response(response: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize generator response."""
        template = {
            "title": "Implementation Plan",
            "description": "",
            "implementation_plan": [],
            "estimated_loc": 0,
            "risk_level": "medium",
            "files_to_change": [],
            "dependencies": [],
            "tests_needed": []
        }

        result = ResponseHandler.ensure_structure(
            response,
            template,
            ["title", "implementation_plan"]
        )

        # Ensure lists are lists
        list_fields = ["implementation_plan", "files_to_change", "dependencies", "tests_needed"]
        for field in list_fields:
            if not isinstance(result.get(field), list):
                result[field] = []

        return result


class RetryHandler:
    """Handle retries with improved prompting."""

    @staticmethod
    async def retry_with_structure(
        model_func,
        original_prompt: str,
        expected_structure: dict[str, Any],
        max_retries: int = 3
    ) -> dict[str, Any] | None:
        """
        Retry model call with increasingly specific prompts.
        
        Args:
            model_func: Async function to call model
            original_prompt: Original prompt
            expected_structure: Expected JSON structure
            max_retries: Maximum retry attempts
            
        Returns:
            Parsed response or None
        """
        prompts = [
            original_prompt,
            f"{original_prompt}\n\nPlease respond with valid JSON only.",
            f"{original_prompt}\n\nYou MUST respond with valid JSON matching this structure:\n{json.dumps(expected_structure, indent=2)}",
            f"CRITICAL: Return ONLY valid JSON, no other text.\nStructure: {json.dumps(expected_structure)}\n\n{original_prompt}"
        ]

        for i, prompt in enumerate(prompts[:max_retries + 1]):
            try:
                response = await model_func(prompt)
                parsed = ResponseHandler.extract_json(response)

                if parsed:
                    return parsed

                logger.warning(f"Retry {i+1}: Failed to parse response")

            except Exception as e:
                logger.error(f"Retry {i+1} failed: {e}")

        return None
