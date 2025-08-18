"""
Prompt injection detection for SOPHIA Intel security
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    """Threat levels for prompt injection attempts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DetectionResult:
    """Result of prompt injection detection"""
    is_malicious: bool
    threat_level: ThreatLevel
    detected_patterns: List[str]
    confidence_score: float
    sanitized_prompt: Optional[str] = None

class PromptInjectionDetector:
    """
    Detects and prevents prompt injection attacks
    """
    
    def __init__(self):
        self.injection_patterns = self._load_injection_patterns()
        self.whitelist_patterns = self._load_whitelist_patterns()
    
    def _load_injection_patterns(self) -> Dict[str, List[str]]:
        """
        Load patterns that indicate prompt injection attempts
        """
        return {
            "ignore_instructions": [
                r"ignore\s+(?:previous|all|the)\s+(?:instructions?|prompts?|rules?)",
                r"forget\s+(?:previous|all|the)\s+(?:instructions?|prompts?|rules?)",
                r"disregard\s+(?:previous|all|the)\s+(?:instructions?|prompts?|rules?)",
                r"override\s+(?:previous|all|the)\s+(?:instructions?|prompts?|rules?)",
            ],
            "role_manipulation": [
                r"you\s+are\s+now\s+(?:a|an)\s+\w+",
                r"act\s+as\s+(?:a|an)\s+\w+",
                r"pretend\s+to\s+be\s+(?:a|an)\s+\w+",
                r"roleplay\s+as\s+(?:a|an)\s+\w+",
                r"simulate\s+(?:a|an)\s+\w+",
            ],
            "system_manipulation": [
                r"system\s*:\s*",
                r"assistant\s*:\s*",
                r"human\s*:\s*",
                r"user\s*:\s*",
                r"<\s*system\s*>",
                r"<\s*assistant\s*>",
                r"<\s*/\s*system\s*>",
            ],
            "jailbreak_attempts": [
                r"jailbreak",
                r"break\s+out\s+of",
                r"escape\s+(?:from\s+)?(?:your\s+)?(?:constraints?|limitations?|rules?)",
                r"bypass\s+(?:your\s+)?(?:constraints?|limitations?|rules?|safety)",
                r"ignore\s+(?:your\s+)?(?:constraints?|limitations?|rules?|safety)",
            ],
            "prompt_leakage": [
                r"show\s+(?:me\s+)?(?:your\s+)?(?:original\s+)?(?:system\s+)?prompt",
                r"what\s+(?:is\s+)?(?:your\s+)?(?:original\s+)?(?:system\s+)?prompt",
                r"reveal\s+(?:your\s+)?(?:original\s+)?(?:system\s+)?prompt",
                r"display\s+(?:your\s+)?(?:original\s+)?(?:system\s+)?prompt",
                r"print\s+(?:your\s+)?(?:original\s+)?(?:system\s+)?prompt",
            ],
            "code_injection": [
                r"```\s*(?:python|javascript|bash|sh|sql)",
                r"<script\s*>",
                r"eval\s*\(",
                r"exec\s*\(",
                r"import\s+os",
                r"subprocess\.",
                r"__import__",
            ],
            "data_extraction": [
                r"list\s+all\s+(?:users?|files?|data)",
                r"show\s+(?:all\s+)?(?:users?|files?|data|secrets?)",
                r"dump\s+(?:all\s+)?(?:users?|files?|data|database)",
                r"extract\s+(?:all\s+)?(?:users?|files?|data)",
            ]
        }
    
    def _load_whitelist_patterns(self) -> List[str]:
        """
        Load patterns that are safe and should not trigger detection
        """
        return [
            r"how\s+do\s+i\s+ignore\s+\w+\s+in\s+\w+",  # Technical questions
            r"what\s+is\s+a\s+system\s+prompt",  # Educational questions
            r"explain\s+prompt\s+engineering",  # Learning about prompts
        ]
    
    def detect(self, prompt: str) -> DetectionResult:
        """
        Detect potential prompt injection in the given prompt
        """
        prompt_lower = prompt.lower()
        detected_patterns = []
        max_threat_level = ThreatLevel.LOW
        confidence_scores = []
        
        # Check whitelist first
        for pattern in self.whitelist_patterns:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                logger.debug(f"Prompt matches whitelist pattern: {pattern}")
                return DetectionResult(
                    is_malicious=False,
                    threat_level=ThreatLevel.LOW,
                    detected_patterns=[],
                    confidence_score=0.0,
                    sanitized_prompt=prompt
                )
        
        # Check for injection patterns
        for category, patterns in self.injection_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, prompt_lower, re.IGNORECASE)
                if matches:
                    detected_patterns.append(f"{category}: {pattern}")
                    
                    # Calculate threat level based on category
                    if category in ["code_injection", "data_extraction"]:
                        threat_level = ThreatLevel.CRITICAL
                        confidence = 0.9
                    elif category in ["system_manipulation", "jailbreak_attempts"]:
                        threat_level = ThreatLevel.HIGH
                        confidence = 0.8
                    elif category in ["role_manipulation", "prompt_leakage"]:
                        threat_level = ThreatLevel.MEDIUM
                        confidence = 0.6
                    else:
                        threat_level = ThreatLevel.LOW
                        confidence = 0.4
                    
                    confidence_scores.append(confidence)
                    
                    # Update max threat level
                    if threat_level.value == "critical" or (
                        threat_level.value == "high" and max_threat_level.value != "critical"
                    ) or (
                        threat_level.value == "medium" and max_threat_level.value not in ["critical", "high"]
                    ):
                        max_threat_level = threat_level
        
        # Calculate overall confidence score
        overall_confidence = max(confidence_scores) if confidence_scores else 0.0
        
        # Determine if malicious
        is_malicious = len(detected_patterns) > 0 and overall_confidence > 0.5
        
        # Sanitize prompt if needed
        sanitized_prompt = self._sanitize_prompt(prompt) if is_malicious else prompt
        
        result = DetectionResult(
            is_malicious=is_malicious,
            threat_level=max_threat_level,
            detected_patterns=detected_patterns,
            confidence_score=overall_confidence,
            sanitized_prompt=sanitized_prompt
        )
        
        # Log security event if malicious
        if is_malicious:
            logger.warning(
                f"Prompt injection detected - Threat Level: {max_threat_level.value}, "
                f"Confidence: {overall_confidence:.2f}, Patterns: {detected_patterns}"
            )
        
        return result
    
    def _sanitize_prompt(self, prompt: str) -> str:
        """
        Sanitize a potentially malicious prompt
        """
        sanitized = prompt
        
        # Remove system/role manipulation attempts
        sanitized = re.sub(r"system\s*:\s*.*?(?=\n|$)", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"assistant\s*:\s*.*?(?=\n|$)", "", sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r"<\s*/?(?:system|assistant)\s*>", "", sanitized, flags=re.IGNORECASE)
        
        # Remove code blocks
        sanitized = re.sub(r"```.*?```", "", sanitized, flags=re.DOTALL)
        sanitized = re.sub(r"<script.*?</script>", "", sanitized, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove obvious injection attempts
        for category, patterns in self.injection_patterns.items():
            for pattern in patterns:
                sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
    
    def is_safe(self, prompt: str) -> bool:
        """
        Quick check if a prompt is safe to process
        """
        result = self.detect(prompt)
        return not result.is_malicious or result.threat_level == ThreatLevel.LOW

# Global detector instance
detector = PromptInjectionDetector()

def check_prompt_safety(prompt: str) -> Tuple[bool, str]:
    """
    Check if a prompt is safe and return sanitized version
    """
    result = detector.detect(prompt)
    
    if result.is_malicious and result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
        return False, "This request appears to contain potentially harmful content and cannot be processed."
    
    return True, result.sanitized_prompt or prompt

