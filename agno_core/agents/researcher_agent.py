from agno_core.agents.base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    category = "research"  # maps to specialized.scout
    creative = False
    strict_quality = False

    def __init__(self):
        super().__init__(name="ResearcherAgent")

