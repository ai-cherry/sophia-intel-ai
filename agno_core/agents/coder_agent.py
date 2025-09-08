from agno_core.agents.base_agent import BaseAgent


class CoderAgent(BaseAgent):
    category = "code_generation"  # maps to router coding
    creative = False
    strict_quality = True

    def __init__(self):
        super().__init__(name="CoderAgent")

