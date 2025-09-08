#!/usr/bin/env python3
"""SOPHIA Core Configuration"""

import os
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

class Phase(Enum):
    """9-phase structure"""
    BRAINSTORM = 1
    RESEARCH = 2
    FILTER = 3
    ANALYZE = 4
    PLAN = 5
    DEBATE = 6
    BUILD = 7
    DOCUMENT = 8
    REMEMBER = 9