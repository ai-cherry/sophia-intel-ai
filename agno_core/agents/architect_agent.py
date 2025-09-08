from agno_core.agents.base_agent import BaseAgent


class ArchitectAgent(BaseAgent):
    category = "analysis"  # maps to router reasoning
    creative = False
    strict_quality = True

    def __init__(self):
        super().__init__(name="ArchitectAgent")

