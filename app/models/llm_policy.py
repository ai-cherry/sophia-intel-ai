from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMPolicy:
    mode: str  # "manual" or "auto"
    # Optional explicit model names (user-specified)
    code_review_model: str | None = None
    refactor_model: str | None = None
    test_model: str | None = None


def get_llm_policy() -> LLMPolicy:
    mode = os.getenv("LLM_SELECTION_MODE", "manual").lower()
    return LLMPolicy(
        mode=mode,
        code_review_model=os.getenv("LLM_CODE_REVIEW_MODEL"),
        refactor_model=os.getenv("LLM_REFACTOR_MODEL"),
        test_model=os.getenv("LLM_TEST_MODEL"),
    )
