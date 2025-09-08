from agno_core.agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    category = "general"  # code review may use general with fallback
    creative = False
    strict_quality = True

    def __init__(self):
        super().__init__(name="ReviewerAgent")

