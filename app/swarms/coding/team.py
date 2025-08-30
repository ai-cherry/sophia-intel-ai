from agno import Team
from app.swarms.coding.agents import (
    create_lead_agent,
    create_coder_a_agent,
    create_coder_b_agent,
    create_critic_agent,
    create_judge_agent
)

def create_coding_team() -> Team:
    """
    Create the Coding Team with all agents and their relationships.
    """
    # Create all agents
    lead = create_lead_agent()
    coder_a = create_coder_a_agent()
    coder_b = create_coder_b_agent()
    critic = create_critic_agent()
    judge = create_judge_agent()
    
    # Create the team
    team = Team(
        name="Coding Team",
        description="A collaborative team for software development tasks",
        agents=[lead, coder_a, coder_b, critic, judge],
        instructions="""
        This team collaborates on software development tasks following this workflow:
        
        1. The Lead analyzes requirements and creates a plan
        2. Coder-A and Coder-B implement features in parallel or sequence
        3. The Critic reviews all code changes
        4. The Judge makes final decisions on quality and merge readiness
        5. The team iterates based on feedback until the task is complete
        
        Key principles:
        - Code quality over speed
        - Test-driven development when applicable
        - Clear documentation and comments
        - Following project conventions and standards
        - Collaborative problem-solving
        """
    )
    
    # Set the lead as the entry point
    team.set_manager(lead)
    
    return team