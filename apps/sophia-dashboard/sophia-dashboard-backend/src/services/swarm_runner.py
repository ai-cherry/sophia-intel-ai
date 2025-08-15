import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path

class SwarmRunner:
    """LangGraph swarm runner with async interface"""
    
    def __init__(self):
        self.jobs_dir = Path("var/swarm_jobs")
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Required environment variables
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        self.github_token = os.getenv('GH_FINE_GRAINED_TOKEN')
        self.mcp_url = os.getenv('MCP_BASE_URL')
        self.mcp_token = os.getenv('MCP_AUTH_TOKEN')
    
    async def dry_run_init(self) -> bool:
        """Dry-run initialization to check if swarm can start"""
        try:
            # Check required environment variables
            if not all([self.openrouter_key, self.github_token, self.mcp_url, self.mcp_token]):
                return False
            
            # Try to import the coding swarm
            from src.agents.coding_swarm import CodingSwarm
            
            # Initialize without actually starting work
            swarm = CodingSwarm(
                openrouter_key=self.openrouter_key,
                github_token=self.github_token,
                mcp_url=self.mcp_url,
                mcp_token=self.mcp_token
            )
            
            return True
        except Exception as e:
            print(f"Swarm dry-run failed: {e}")
            return False
    
    async def create_plan(self, repo: str, goal: str, constraints: Optional[str] = None) -> str:
        """Create a new planning job"""
        job_id = str(uuid.uuid4())
        
        job_data = {
            "job_id": job_id,
            "repo": repo,
            "goal": goal,
            "constraints": constraints,
            "status": "planning",
            "created_at": datetime.now().isoformat(),
            "events": [],
            "agents": {
                "planner": {"status": "pending", "started_at": None, "completed_at": None},
                "coder": {"status": "pending", "started_at": None, "completed_at": None},
                "reviewer": {"status": "pending", "started_at": None, "completed_at": None},
                "integrator": {"status": "pending", "started_at": None, "completed_at": None}
            }
        }
        
        # Save job data
        job_file = self.jobs_dir / f"{job_id}.json"
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
        
        # Start planning in background
        asyncio.create_task(self._run_planning_phase(job_id))
        
        return job_id
    
    async def implement_plan(self, job_id: str) -> Dict[str, Any]:
        """Implement a planned job"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            raise ValueError(f"Job {job_id} not found")
        
        with open(job_file, 'r') as f:
            job_data = json.load(f)
        
        if job_data["status"] != "planned":
            raise ValueError(f"Job {job_id} is not in planned state")
        
        # Update status to implementing
        job_data["status"] = "implementing"
        job_data["updated_at"] = datetime.now().isoformat()
        
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
        
        # Start implementation in background
        asyncio.create_task(self._run_implementation_phase(job_id))
        
        return {"status": "implementing", "job_id": job_id}
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get current job status"""
        job_file = self.jobs_dir / f"{job_id}.json"
        if not job_file.exists():
            raise ValueError(f"Job {job_id} not found")
        
        with open(job_file, 'r') as f:
            return json.load(f)
    
    async def _run_planning_phase(self, job_id: str):
        """Run the planning phase"""
        try:
            job_file = self.jobs_dir / f"{job_id}.json"
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            # Update planner status
            job_data["agents"]["planner"]["status"] = "running"
            job_data["agents"]["planner"]["started_at"] = datetime.now().isoformat()
            job_data["events"].append({
                "timestamp": datetime.now().isoformat(),
                "agent": "planner",
                "event": "started",
                "message": "Planning phase initiated"
            })
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
            
            # Simulate planning work (in real implementation, call the actual swarm)
            await asyncio.sleep(2)  # Simulate planning time
            
            # Complete planning
            job_data["agents"]["planner"]["status"] = "completed"
            job_data["agents"]["planner"]["completed_at"] = datetime.now().isoformat()
            job_data["status"] = "planned"
            job_data["events"].append({
                "timestamp": datetime.now().isoformat(),
                "agent": "planner",
                "event": "completed",
                "message": f"Planning completed for goal: {job_data['goal']}"
            })
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
                
        except Exception as e:
            # Handle planning failure
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            job_data["status"] = "failed"
            job_data["agents"]["planner"]["status"] = "failed"
            job_data["error"] = str(e)
            job_data["events"].append({
                "timestamp": datetime.now().isoformat(),
                "agent": "planner",
                "event": "failed",
                "message": f"Planning failed: {str(e)}"
            })
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
    
    async def _run_implementation_phase(self, job_id: str):
        """Run the implementation phase (coder -> reviewer -> integrator)"""
        try:
            job_file = self.jobs_dir / f"{job_id}.json"
            
            # Run coder phase
            await self._run_agent_phase(job_id, "coder", "Generating code changes")
            
            # Run reviewer phase
            await self._run_agent_phase(job_id, "reviewer", "Reviewing generated code")
            
            # Run integrator phase
            await self._run_agent_phase(job_id, "integrator", "Creating branch and PR")
            
            # Complete the job
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            job_data["status"] = "completed"
            job_data["completed_at"] = datetime.now().isoformat()
            job_data["events"].append({
                "timestamp": datetime.now().isoformat(),
                "agent": "system",
                "event": "completed",
                "message": "All agents completed successfully",
                "branch_url": f"https://github.com/{job_data['repo']}/tree/feat/auto/{job_id[:8]}",
                "pr_url": f"https://github.com/{job_data['repo']}/pull/123"  # Mock PR URL
            })
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
                
        except Exception as e:
            # Handle implementation failure
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            job_data["status"] = "failed"
            job_data["error"] = str(e)
            job_data["events"].append({
                "timestamp": datetime.now().isoformat(),
                "agent": "system",
                "event": "failed",
                "message": f"Implementation failed: {str(e)}"
            })
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
    
    async def _run_agent_phase(self, job_id: str, agent: str, message: str):
        """Run a single agent phase"""
        job_file = self.jobs_dir / f"{job_id}.json"
        
        with open(job_file, 'r') as f:
            job_data = json.load(f)
        
        # Start agent
        job_data["agents"][agent]["status"] = "running"
        job_data["agents"][agent]["started_at"] = datetime.now().isoformat()
        job_data["events"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "event": "started",
            "message": message
        })
        
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)
        
        # Simulate agent work
        await asyncio.sleep(3)  # Simulate processing time
        
        # Complete agent
        job_data["agents"][agent]["status"] = "completed"
        job_data["agents"][agent]["completed_at"] = datetime.now().isoformat()
        job_data["events"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "event": "completed",
            "message": f"{agent.capitalize()} phase completed"
        })
        
        with open(job_file, 'w') as f:
            json.dump(job_data, f, indent=2)

