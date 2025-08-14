"""
Swarm Integration Module for MCP Servers
Handles communication between MCP servers and the Swarm system
"""
from typing import Dict, Any, Optional, List
import json
import time
import os
import asyncio
from datetime import datetime
from pathlib import Path
from loguru import logger

class SwarmIntegration:
    """
    Integration between MCP servers and Swarm system
    
    Features:
    - Telemetry recording to .swarm_handoffs.log
    - Circuit breaker implementation (hop/time/error limits)
    - Handoff processing between agents
    - Session status tracking
    - Performance monitoring
    """
    
    def __init__(self):
        # Configuration from environment variables
        self.handoff_log = os.getenv("SWARM_HANDOFFS_LOG", ".swarm_handoffs.log")
        self.max_hops = int(os.getenv("MAX_SWARM_HOPS", "12"))
        self.max_time_minutes = int(os.getenv("MAX_STAGE_TIME_MINUTES", "10"))
        self.max_errors = int(os.getenv("MAX_ERRORS", "3"))
        self.min_artifact_chars = int(os.getenv("MIN_ARTIFACT_CHARS", "50"))
        
        # Ensure log directory exists
        Path(self.handoff_log).parent.mkdir(exist_ok=True)
        
        # Initialize performance tracking
        self._session_cache = {}
        self._lock = asyncio.Lock()
        
        logger.info(f"SwarmIntegration initialized with log: {self.handoff_log}")
        
    async def record_telemetry(self, data: Dict[str, Any]) -> None:
        """
        Record telemetry data to swarm handoffs log
        
        Args:
            data: Telemetry data to record
        """
        try:
            # Add standard fields
            data["timestamp"] = data.get("timestamp", time.time())
            data["type"] = data.get("type", "mcp_telemetry")
            data["node_id"] = os.getenv("NODE_ID", "unknown")
            
            # Format for logging
            log_entry = json.dumps(data, separators=(',', ':'))
            
            # Write to log file (async-safe)
            async with self._lock:
                with open(self.handoff_log, "a") as f:
                    f.write(log_entry + "\n")
                    
        except Exception as e:
            logger.error(f"Failed to record telemetry: {e}")
    
    async def process_handoff(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a handoff between swarm agents
        
        Args:
            data: Handoff data containing session_id, from_stage, to_stage, artifact
            
        Returns:
            Dict containing handoff result
        """
        session_id = data.get("session_id")
        from_stage = data.get("from_stage")
        to_stage = data.get("to_stage")
        artifact = data.get("artifact", "")
        service = data.get("service", "unknown")
        
        # Validate required fields
        if not session_id or not isinstance(session_id, str):
            return {
                "status": "error",
                "error": "session_id is required and must be a string"
            }
        
        if not to_stage or not isinstance(to_stage, str):
            return {
                "status": "error",
                "error": "to_stage is required and must be a string",
                "session_id": session_id
            }
        
        logger.info(f"Processing handoff {from_stage} → {to_stage} for session {session_id}")
        
        # Record the handoff attempt
        handoff_data = {
            "type": "handoff",
            "session_id": session_id,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "artifact_size": len(artifact),
            "service": service,
            "timestamp": time.time()
        }
        
        try:
            # Apply circuit breakers
            circuit_check = await self._check_circuit_breakers(session_id)
            if circuit_check["broken"]:
                handoff_data.update({
                    "status": "circuit_breaker_triggered",
                    "circuit_breaker": circuit_check["reason"]
                })
                await self.record_telemetry(handoff_data)
                
                return {
                    "status": "error",
                    "error": f"Circuit breaker triggered: {circuit_check['reason']}",
                    "session_id": session_id,
                    "circuit_breaker": circuit_check["reason"]
                }
                
            # Validate artifact
            if len(artifact) < self.min_artifact_chars:
                handoff_data.update({
                    "status": "artifact_validation_failed",
                    "circuit_breaker": "artifact_validation"
                })
                await self.record_telemetry(handoff_data)
                
                return {
                    "status": "error",
                    "error": f"Artifact too small: {len(artifact)} chars (min: {self.min_artifact_chars})",
                    "session_id": session_id
                }
                
            # Record successful handoff
            handoff_data.update({"status": "success"})
            await self.record_telemetry(handoff_data)
            
            # Update session cache
            await self._update_session_cache(session_id, to_stage)
            
            return {
                "status": "success",
                "session_id": session_id,
                "from_stage": from_stage,
                "to_stage": to_stage,
                "artifact_size": len(artifact),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error processing handoff: {e}")
            handoff_data.update({
                "status": "error",
                "error": str(e)
            })
            await self.record_telemetry(handoff_data)
            
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
        
    async def get_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current status of a swarm session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict containing session status
        """
        try:
            handoffs = []
            errors = []
            
            # Read handoffs log
            if os.path.exists(self.handoff_log):
                with open(self.handoff_log, "r") as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            if data.get("session_id") == session_id:
                                if data.get("type") == "handoff":
                                    handoffs.append(data)
                                elif data.get("type") in ["error", "exception"]:
                                    errors.append(data)
                        except json.JSONDecodeError:
                            continue
                        
            if not handoffs:
                return {
                    "status": "not_found",
                    "session_id": session_id,
                    "message": "No handoffs found for this session"
                }
                
            # Sort by timestamp
            handoffs.sort(key=lambda x: x.get("timestamp", 0))
            errors.sort(key=lambda x: x.get("timestamp", 0))
            
            # Determine current stage
            last_handoff = handoffs[-1]
            current_stage = last_handoff.get("to_stage", "unknown")
            
            # Check if terminated
            is_terminated = (
                last_handoff.get("status") == "circuit_breaker_triggered" or
                last_handoff.get("circuit_breaker") is not None
            )
            
            status = "terminated" if is_terminated else "active"
            
            return {
                "status": status,
                "session_id": session_id,
                "current_stage": current_stage,
                "hop_count": len(handoffs),
                "error_count": len(errors),
                "start_time": handoffs[0].get("timestamp") if handoffs else None,
                "last_activity": last_handoff.get("timestamp"),
                "elapsed_seconds": (
                    time.time() - handoffs[0].get("timestamp", time.time())
                    if handoffs else 0
                ),
                "circuit_breaker": last_handoff.get("circuit_breaker"),
                "services_used": list(set(h.get("service", "unknown") for h in handoffs))
            }
            
        except Exception as e:
            logger.error(f"Error getting swarm status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }
    
    async def get_telemetry_history(self, session_id: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get telemetry history for a session
        
        Args:
            session_id: Session identifier
            limit: Maximum number of entries to return
            
        Returns:
            Dict containing telemetry entries
        """
        try:
            entries = []
            
            if os.path.exists(self.handoff_log):
                with open(self.handoff_log, "r") as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            if data.get("session_id") == session_id:
                                entries.append(data)
                        except json.JSONDecodeError:
                            continue
            
            # Sort by timestamp (newest first) and limit
            entries.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
            entries = entries[:limit]
            
            return {
                "session_id": session_id,
                "entries": entries,
                "count": len(entries),
                "limited": len(entries) == limit
            }
            
        except Exception as e:
            logger.error(f"Error getting telemetry history: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "entries": [],
                "count": 0
            }
    
    async def _check_circuit_breakers(self, session_id: str) -> Dict[str, Any]:
        """
        Check if any circuit breakers should trigger
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict with broken status and reason
        """
        try:
            status = await self.get_status(session_id)
            
            # Already terminated
            if status.get("status") == "terminated":
                return {"broken": True, "reason": "already_terminated"}
                
            # Hop limit
            if status.get("hop_count", 0) >= self.max_hops:
                return {"broken": True, "reason": "hop_limit_exceeded"}
                
            # Time limit
            elapsed_minutes = status.get("elapsed_seconds", 0) / 60
            if elapsed_minutes >= self.max_time_minutes:
                return {"broken": True, "reason": "time_limit_exceeded"}
                
            # Error limit
            if status.get("error_count", 0) >= self.max_errors:
                return {"broken": True, "reason": "error_limit_exceeded"}
                
            return {"broken": False, "reason": None}
            
        except Exception as e:
            logger.error(f"Error checking circuit breakers: {e}")
            return {"broken": True, "reason": f"circuit_breaker_check_failed: {e}"}
    
    async def _update_session_cache(self, session_id: str, current_stage: str):
        """Update in-memory session cache for performance"""
        async with self._lock:
            self._session_cache[session_id] = {
                "current_stage": current_stage,
                "last_update": time.time()
            }
            
            # Clean old entries (keep last 1000 sessions)
            if len(self._session_cache) > 1000:
                sorted_items = sorted(
                    self._session_cache.items(),
                    key=lambda x: x[1]["last_update"]
                )
                # Keep newest 500
                self._session_cache = dict(sorted_items[-500:])
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system-wide Swarm metrics
        
        Returns:
            Dict containing system metrics
        """
        try:
            active_sessions = set()
            total_handoffs = 0
            total_errors = 0
            services_used = set()
            
            if os.path.exists(self.handoff_log):
                # Count last hour activity
                one_hour_ago = time.time() - 3600
                
                with open(self.handoff_log, "r") as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            timestamp = data.get("timestamp", 0)
                            
                            if timestamp >= one_hour_ago:
                                session_id = data.get("session_id")
                                if session_id:
                                    active_sessions.add(session_id)
                                
                                if data.get("type") == "handoff":
                                    total_handoffs += 1
                                    services_used.add(data.get("service", "unknown"))
                                elif data.get("type") in ["error", "exception"]:
                                    total_errors += 1
                                    
                        except json.JSONDecodeError:
                            continue
            
            return {
                "active_sessions": len(active_sessions),
                "total_handoffs_last_hour": total_handoffs,
                "total_errors_last_hour": total_errors,
                "services_active": list(services_used),
                "circuit_breaker_limits": {
                    "max_hops": self.max_hops,
                    "max_time_minutes": self.max_time_minutes,
                    "max_errors": self.max_errors,
                    "min_artifact_chars": self.min_artifact_chars
                },
                "log_file": self.handoff_log,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "error": str(e),
                "timestamp": time.time()
            }