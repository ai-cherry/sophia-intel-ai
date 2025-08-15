"""
Agent Swarm API for SOPHIA Intel

Provides REST API endpoints for interacting with the agent swarm:
- Start development missions
- Monitor mission progress
- Get swarm status and metrics
- Cancel missions
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

from .swarm.swarm_orchestrator import SwarmOrchestrator, Priority


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global swarm orchestrator instance
swarm: Optional[SwarmOrchestrator] = None


@app.before_first_request
async def initialize_swarm():
    """Initialize the swarm orchestrator"""
    global swarm
    if swarm is None:
        swarm = SwarmOrchestrator()
        await swarm.initialize()
        logger.info("Agent Swarm initialized")


@app.route('/api/swarm/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "SOPHIA Intel Agent Swarm",
        "timestamp": datetime.utcnow().isoformat(),
        "swarm_running": swarm is not None and swarm.is_running
    })


@app.route('/api/swarm/status', methods=['GET'])
async def get_swarm_status():
    """Get overall swarm status and metrics"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        status = await swarm.get_swarm_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting swarm status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/swarm/missions', methods=['POST'])
async def start_mission():
    """Start a new development mission"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'description' not in data:
            return jsonify({"error": "Mission description is required"}), 400
        
        description = data['description']
        requirements = data.get('requirements', {})
        priority_str = data.get('priority', 'medium').lower()
        
        # Convert priority
        priority_mapping = {
            'low': Priority.LOW,
            'medium': Priority.MEDIUM,
            'high': Priority.HIGH,
            'critical': Priority.CRITICAL
        }
        priority = priority_mapping.get(priority_str, Priority.MEDIUM)
        
        # Start mission
        mission_id = await swarm.start_mission(
            description=description,
            requirements=requirements,
            priority=priority
        )
        
        return jsonify({
            "mission_id": mission_id,
            "status": "queued",
            "message": "Mission started successfully"
        }), 201
        
    except Exception as e:
        logger.error(f"Error starting mission: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/swarm/missions/<mission_id>', methods=['GET'])
async def get_mission_status(mission_id: str):
    """Get the status of a specific mission"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        status = await swarm.get_mission_status(mission_id)
        return jsonify(status)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting mission status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/swarm/missions/<mission_id>', methods=['DELETE'])
async def cancel_mission(mission_id: str):
    """Cancel a mission"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        success = await swarm.cancel_mission(mission_id)
        if success:
            return jsonify({
                "mission_id": mission_id,
                "status": "cancelled",
                "message": "Mission cancelled successfully"
            })
        else:
            return jsonify({"error": "Mission not found"}), 404
            
    except Exception as e:
        logger.error(f"Error cancelling mission: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/swarm/missions', methods=['GET'])
async def list_missions():
    """List all missions with optional filtering"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        # Get swarm status to access missions
        swarm_status = await swarm.get_swarm_status()
        
        missions = []
        
        # Add active missions
        for mission_id in swarm.active_missions:
            mission_status = await swarm.get_mission_status(mission_id)
            if not status_filter or mission_status['status'] == status_filter:
                missions.append(mission_status)
        
        # Add completed missions (limited)
        for mission in swarm.completed_missions[-limit:]:
            mission_status = swarm._format_mission_status(mission)
            if not status_filter or mission_status['status'] == status_filter:
                missions.append(mission_status)
        
        # Add queued missions
        for mission in swarm.mission_queue:
            mission_status = swarm._format_mission_status(mission)
            if not status_filter or mission_status['status'] == status_filter:
                missions.append(mission_status)
        
        # Sort by created_at (most recent first)
        missions.sort(key=lambda m: m['created_at'], reverse=True)
        
        return jsonify({
            "missions": missions[:limit],
            "total": len(missions),
            "filtered": status_filter is not None
        })
        
    except Exception as e:
        logger.error(f"Error listing missions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/swarm/agents', methods=['GET'])
async def list_agents():
    """List all agents and their capabilities"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        agents = []
        for agent in swarm.agent_pool:
            agent_info = agent.get_status()
            agents.append(agent_info)
        
        return jsonify({
            "agents": agents,
            "total": len(agents)
        })
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/swarm/agents/<agent_name>/tasks', methods=['GET'])
async def get_agent_tasks(agent_name: str):
    """Get tasks for a specific agent"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        # Find agent by name
        target_agent = None
        for agent in swarm.agent_pool:
            if agent.name == agent_name:
                target_agent = agent
                break
        
        if not target_agent:
            return jsonify({"error": "Agent not found"}), 404
        
        # Get agent tasks
        current_tasks = [
            {
                "id": task.id,
                "type": task.type,
                "description": task.description,
                "status": task.status.value,
                "priority": task.priority.value,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "started_at": task.started_at.isoformat() if task.started_at else None
            }
            for task in target_agent.current_tasks.values()
        ]
        
        completed_tasks = [
            {
                "id": task.id,
                "type": task.type,
                "description": task.description,
                "status": task.status.value,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "duration_seconds": (
                    (task.completed_at - task.started_at).total_seconds()
                    if task.completed_at and task.started_at else 0
                )
            }
            for task in target_agent.completed_tasks[-10:]  # Last 10 completed tasks
        ]
        
        return jsonify({
            "agent_name": agent_name,
            "current_tasks": current_tasks,
            "completed_tasks": completed_tasks,
            "metrics": target_agent.metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting agent tasks: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/swarm/demo', methods=['POST'])
async def demo_mission():
    """Start a demo mission for testing"""
    if not swarm:
        return jsonify({"error": "Swarm not initialized"}), 500
    
    try:
        # Create a demo mission
        demo_description = "Create a simple REST API with user authentication"
        demo_requirements = {
            "framework": "flask",
            "features": [
                "User registration and login",
                "JWT token authentication",
                "Protected endpoints",
                "Input validation",
                "Error handling"
            ],
            "database": "sqlite",
            "testing": True,
            "documentation": True
        }
        
        mission_id = await swarm.start_mission(
            description=demo_description,
            requirements=demo_requirements,
            priority=Priority.HIGH
        )
        
        return jsonify({
            "mission_id": mission_id,
            "status": "queued",
            "message": "Demo mission started successfully",
            "description": demo_description,
            "requirements": demo_requirements
        }), 201
        
    except Exception as e:
        logger.error(f"Error starting demo mission: {e}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Initialize swarm
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize_swarm())
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5001, debug=False)

