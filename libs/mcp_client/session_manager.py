"""
SOPHIA Session Manager
Manages persistent sessions with context continuity across SOPHIA restarts
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from .sophia_client import SophiaMCPClient, MCPServerError

logger = logging.getLogger(__name__)


class SophiaSessionManager:
    """
    Session manager that provides persistent context across SOPHIA sessions
    with intelligent context loading and session continuity features.
    """

    def __init__(self, 
                 sessions_dir: str = ".sophia_sessions",
                 mcp_port: int = 8000,
                 max_sessions: int = 100):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self.mcp_port = mcp_port
        self.max_sessions = max_sessions
        
        self.current_session: Optional[str] = None
        self.mcp_client: Optional[SophiaMCPClient] = None
        self.session_metadata = {}
        self.active_sessions = {}
        
        # Load existing sessions
        self._load_session_registry()

    async def start_session(self, 
                          session_id: Optional[str] = None,
                          project_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new SOPHIA session or resume an existing one
        
        Args:
            session_id: Optional session ID to resume, creates new if None
            project_context: Optional project context (repo path, etc.)
            
        Returns:
            The session ID
        """
        if session_id is None:
            session_id = f"sophia_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        logger.info(f"Starting SOPHIA session: {session_id}")
        
        try:
            # Initialize MCP client for this session
            self.mcp_client = SophiaMCPClient(session_id, self.mcp_port)
            await self.mcp_client.connect()
            
            self.current_session = session_id
            
            # Initialize session metadata
            session_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "project_context": project_context or {},
                "activity_count": 0,
                "context_entries": 0
            }
            
            # Load previous session context if resuming
            if session_id in self.session_metadata:
                logger.info(f"Resuming existing session: {session_id}")
                existing_data = self.session_metadata[session_id]
                session_data.update(existing_data)
                session_data["last_active"] = datetime.now().isoformat()
                
                # Load context from previous session
                await self._load_session_context(session_id)
            else:
                logger.info(f"Created new session: {session_id}")
            
            self.session_metadata[session_id] = session_data
            self.active_sessions[session_id] = {
                "mcp_client": self.mcp_client,
                "start_time": time.time(),
                "activity_count": 0
            }
            
            # Save session registry
            await self._save_session_registry()
            
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to start session {session_id}: {e}")
            if self.mcp_client:
                await self.mcp_client.disconnect()
            raise

    async def end_session(self, session_id: Optional[str] = None):
        """
        End the current or specified session
        
        Args:
            session_id: Optional session ID, uses current if None
        """
        target_session = session_id or self.current_session
        if not target_session:
            logger.warning("No session to end")
            return
        
        logger.info(f"Ending SOPHIA session: {target_session}")
        
        try:
            # Store session summary
            if target_session in self.active_sessions:
                active_session = self.active_sessions[target_session]
                session_data = self.session_metadata.get(target_session, {})
                
                # Calculate session duration
                duration = time.time() - active_session["start_time"]
                session_data.update({
                    "ended_at": datetime.now().isoformat(),
                    "duration_seconds": duration,
                    "final_activity_count": active_session["activity_count"]
                })
                
                # Store session summary in context
                if self.mcp_client:
                    await self.mcp_client.store_context(
                        content=json.dumps(session_data, default=str),
                        context_type="session_summary",
                        metadata={
                            "session_duration": duration,
                            "activity_count": active_session["activity_count"]
                        }
                    )
                
                # Clean up active session
                del self.active_sessions[target_session]
            
            # Disconnect MCP client
            if self.mcp_client and target_session == self.current_session:
                await self.mcp_client.disconnect()
                self.mcp_client = None
                self.current_session = None
            
            # Save updated metadata
            await self._save_session_registry()
            
        except Exception as e:
            logger.error(f"Error ending session {target_session}: {e}")

    async def get_context_for_action(self, 
                                   action_description: str,
                                   file_path: Optional[str] = None,
                                   max_context: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant context for a specific action
        
        Args:
            action_description: Description of the action being performed
            file_path: Optional file path for file-specific context
            max_context: Maximum number of context entries to return
            
        Returns:
            List of relevant context entries
        """
        if not self.mcp_client:
            logger.warning("No active session - cannot retrieve context")
            return []
        
        try:
            # Get relevant context from MCP client
            context = await self.mcp_client.get_relevant_context(
                current_action=action_description,
                file_path=file_path
            )
            
            # Update activity count
            if self.current_session in self.active_sessions:
                self.active_sessions[self.current_session]["activity_count"] += 1
            
            return context[:max_context]
            
        except Exception as e:
            logger.error(f"Failed to get context for action: {e}")
            return []

    async def store_activity(self, 
                           activity_type: str,
                           description: str,
                           data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store an activity in the current session context
        
        Args:
            activity_type: Type of activity (e.g., "tool_usage", "code_change")
            description: Description of the activity
            data: Optional additional data
            
        Returns:
            Storage confirmation
        """
        if not self.mcp_client:
            logger.warning("No active session - cannot store activity")
            return {"success": False, "error": "No active session"}
        
        try:
            activity_data = {
                "activity_type": activity_type,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.current_session,
                **(data or {})
            }
            
            result = await self.mcp_client.store_context(
                content=json.dumps(activity_data, default=str),
                context_type=activity_type,
                metadata={
                    "activity_type": activity_type,
                    "session_id": self.current_session
                }
            )
            
            # Update session stats
            if self.current_session in self.session_metadata:
                self.session_metadata[self.current_session]["context_entries"] += 1
                self.session_metadata[self.current_session]["last_active"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to store activity: {e}")
            return {"success": False, "error": str(e)}

    async def get_session_stats(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for the current or specified session
        
        Args:
            session_id: Optional session ID, uses current if None
            
        Returns:
            Session statistics
        """
        target_session = session_id or self.current_session
        if not target_session:
            return {"error": "No session specified"}
        
        stats = {
            "session_id": target_session,
            "is_active": target_session in self.active_sessions,
            "metadata": self.session_metadata.get(target_session, {})
        }
        
        if self.mcp_client and target_session == self.current_session:
            stats["mcp_stats"] = self.mcp_client.get_stats()
        
        return stats

    async def list_sessions(self, 
                          active_only: bool = False,
                          limit: int = 20) -> List[Dict[str, Any]]:
        """
        List available sessions
        
        Args:
            active_only: Only return active sessions
            limit: Maximum number of sessions to return
            
        Returns:
            List of session information
        """
        sessions = []
        
        for session_id, metadata in self.session_metadata.items():
            if active_only and session_id not in self.active_sessions:
                continue
            
            session_info = {
                "session_id": session_id,
                "is_active": session_id in self.active_sessions,
                **metadata
            }
            sessions.append(session_info)
        
        # Sort by last active time (most recent first)
        sessions.sort(
            key=lambda x: x.get("last_active", ""),
            reverse=True
        )
        
        return sessions[:limit]

    async def cleanup_old_sessions(self, 
                                 max_age_days: int = 30,
                                 keep_active: bool = True) -> int:
        """
        Clean up old sessions to prevent storage bloat
        
        Args:
            max_age_days: Maximum age of sessions to keep
            keep_active: Whether to keep active sessions regardless of age
            
        Returns:
            Number of sessions cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        sessions_to_remove = []
        
        for session_id, metadata in self.session_metadata.items():
            if keep_active and session_id in self.active_sessions:
                continue
            
            last_active = metadata.get("last_active")
            if last_active:
                try:
                    last_active_date = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    if last_active_date < cutoff_date:
                        sessions_to_remove.append(session_id)
                except Exception as e:
                    logger.warning(f"Invalid date format for session {session_id}: {e}")
        
        # Remove old sessions
        for session_id in sessions_to_remove:
            del self.session_metadata[session_id]
            logger.info(f"Cleaned up old session: {session_id}")
        
        if sessions_to_remove:
            await self._save_session_registry()
        
        return len(sessions_to_remove)

    async def _load_session_context(self, session_id: str):
        """Load context for a resumed session"""
        try:
            if self.mcp_client:
                # Query for recent session context
                context = await self.mcp_client.query_context(
                    f"session:{session_id}",
                    top_k=10,
                    threshold=0.5
                )
                logger.info(f"Loaded {len(context)} context entries for session {session_id}")
        except Exception as e:
            logger.warning(f"Failed to load session context: {e}")

    def _load_session_registry(self):
        """Load the session registry from disk"""
        registry_file = self.sessions_dir / "session_registry.json"
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    self.session_metadata = json.load(f)
                logger.info(f"Loaded {len(self.session_metadata)} sessions from registry")
            except Exception as e:
                logger.error(f"Failed to load session registry: {e}")
                self.session_metadata = {}
        else:
            self.session_metadata = {}

    async def _save_session_registry(self):
        """Save the session registry to disk"""
        registry_file = self.sessions_dir / "session_registry.json"
        try:
            with open(registry_file, 'w') as f:
                json.dump(self.session_metadata, f, indent=2, default=str)
            logger.debug("Session registry saved")
        except Exception as e:
            logger.error(f"Failed to save session registry: {e}")

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.current_session:
            await self.end_session()