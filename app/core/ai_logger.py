"""
AI-Powered Logging System
Replaces all print statements with intelligent, structured logging
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import traceback
import uuid
from collections import deque

from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str
    context: Dict[str, Any] = {}
    trace_id: str
    source: str
    line_number: int = None
    function_name: str = None
    ai_analysis: Optional[Dict] = None


class PatternAnalyzer:
    """Analyzes log patterns for anomalies"""
    
    def __init__(self, window_size: int = 100):
        self.log_window = deque(maxlen=window_size)
        self.patterns = {}
        self.anomalies = []
    
    def add_log(self, log_entry: LogEntry):
        self.log_window.append(log_entry)
        self._analyze_patterns()
    
    def _analyze_patterns(self):
        """Analyze recent logs for patterns"""
        if len(self.log_window) < 10:
            return
        
        # Count error frequency
        error_count = sum(1 for log in self.log_window if log.level == "ERROR")
        if error_count > len(self.log_window) * 0.3:  # >30% errors
            self.anomalies.append({
                "type": "high_error_rate",
                "severity": "high",
                "details": f"{error_count} errors in last {len(self.log_window)} logs"
            })
        
        # Detect repeated messages
        messages = [log.message for log in self.log_window]
        for msg in set(messages):
            if messages.count(msg) > 5:
                self.anomalies.append({
                    "type": "repeated_message",
                    "severity": "medium",
                    "message": msg,
                    "count": messages.count(msg)
                })
    
    def get_anomalies(self) -> List[Dict]:
        anomalies = self.anomalies.copy()
        self.anomalies.clear()
        return anomalies


class AILogger:
    """
    AI-Powered Logger that replaces all print statements
    Provides intelligent analysis and pattern detection
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            # Setup standard Python logger
            self.logger = logging.getLogger("AILogger")
            self.logger.setLevel(logging.DEBUG)
            
            # Console handler with formatting
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
            
            # File handler for persistent logs
            file_handler = logging.FileHandler('logs/ai_system.log')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # AI components
            self.llm = ChatOpenAI(model="gpt-4-turbo")
            self.pattern_analyzer = PatternAnalyzer()
            
            # Log history for context
            self.recent_logs = deque(maxlen=100)
            self.error_context = deque(maxlen=20)
            
            # Background task for AI analysis
            self.analysis_queue = asyncio.Queue()
            self.analysis_task = None
            
            self.initialized = True
    
    def generate_trace_id(self) -> str:
        """Generate unique trace ID for request tracking"""
        return str(uuid.uuid4())[:8]
    
    def _get_caller_info(self) -> Dict:
        """Get information about the calling code"""
        import inspect
        
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back if frame else None
        
        if caller_frame:
            return {
                "function": caller_frame.f_code.co_name,
                "file": caller_frame.f_code.co_filename.split("/")[-1],
                "line": caller_frame.f_lineno
            }
        return {}
    
    def log(self, level: LogLevel, message: str, context: Dict = None, trace_id: str = None):
        """
        Main logging method that replaces print()
        
        Usage:
            logger.log(LogLevel.INFO, "Task completed", {"task_id": "123"})
        """
        
        # Get caller information
        caller_info = self._get_caller_info()
        
        # Create structured log entry
        log_entry = LogEntry(
            timestamp=datetime.now(),
            level=level.name,
            message=message,
            context=context or {},
            trace_id=trace_id or self.generate_trace_id(),
            source=caller_info.get("file", "unknown"),
            line_number=caller_info.get("line"),
            function_name=caller_info.get("function")
        )
        
        # Add to pattern analyzer
        self.pattern_analyzer.add_log(log_entry)
        
        # Store in history
        self.recent_logs.append(log_entry)
        if level.value >= LogLevel.ERROR.value:
            self.error_context.append(log_entry)
        
        # Log using standard logger
        self._standard_log(level, log_entry)
        
        # Queue for AI analysis if significant
        if level.value >= LogLevel.WARNING.value:
            asyncio.create_task(self._queue_for_analysis(log_entry))
        
        return log_entry
    
    def _standard_log(self, level: LogLevel, entry: LogEntry):
        """Log using Python's standard logger"""
        
        # Format message with context
        msg = entry.message
        if entry.context:
            msg += f" | Context: {json.dumps(entry.context)}"
        msg += f" | Trace: {entry.trace_id}"
        
        if level == LogLevel.DEBUG:
            self.logger.debug(msg)
        elif level == LogLevel.INFO:
            self.logger.info(msg)
        elif level == LogLevel.WARNING:
            self.logger.warning(msg)
        elif level == LogLevel.ERROR:
            self.logger.error(msg)
        elif level == LogLevel.CRITICAL:
            self.logger.critical(msg)
    
    async def _queue_for_analysis(self, log_entry: LogEntry):
        """Queue log entry for AI analysis"""
        await self.analysis_queue.put(log_entry)
        
        # Start analysis task if not running
        if self.analysis_task is None or self.analysis_task.done():
            self.analysis_task = asyncio.create_task(self._analysis_worker())
    
    async def _analysis_worker(self):
        """Background worker for AI analysis"""
        
        batch = []
        while True:
            try:
                # Collect batch of logs for analysis
                log_entry = await asyncio.wait_for(
                    self.analysis_queue.get(), 
                    timeout=5.0
                )
                batch.append(log_entry)
                
                # Process batch if large enough or timeout
                if len(batch) >= 5:
                    await self._ai_analyze_batch(batch)
                    batch.clear()
                    
            except asyncio.TimeoutError:
                # Process any pending logs
                if batch:
                    await self._ai_analyze_batch(batch)
                    batch.clear()
                break
            except Exception as e:
                self.error(f"Analysis worker error: {e}")
    
    async def _ai_analyze_batch(self, logs: List[LogEntry]):
        """AI analyzes a batch of logs"""
        
        try:
            # Check for anomalies first
            anomalies = self.pattern_analyzer.get_anomalies()
            
            # Prepare context for AI
            context = {
                "recent_errors": [
                    {"message": log.message, "context": log.context}
                    for log in self.error_context
                ],
                "anomalies": anomalies,
                "logs_to_analyze": [
                    {
                        "level": log.level,
                        "message": log.message,
                        "context": log.context
                    }
                    for log in logs
                ]
            }
            
            prompt = f"""
            Analyze these system logs and provide insights:
            
            {json.dumps(context, indent=2, default=str)}
            
            Provide:
            1. Root cause analysis for any errors
            2. Performance implications
            3. Suggested actions
            4. Severity assessment (1-10)
            
            Format as JSON with keys: root_cause, performance_impact, actions, severity
            """
            
            response = await self.llm.ainvoke(prompt)
            analysis = json.loads(response.content)
            
            # Take action based on severity
            if analysis.get("severity", 0) >= 8:
                await self._trigger_alert(analysis)
            
            # Log the analysis
            self.info(
                "AI Analysis Complete",
                {"analysis": analysis, "logs_analyzed": len(logs)}
            )
            
        except Exception as e:
            self.error(f"AI analysis failed: {e}")
    
    async def _trigger_alert(self, analysis: Dict):
        """Trigger alert for high-severity issues"""
        
        alert = {
            "timestamp": datetime.now().isoformat(),
            "severity": analysis.get("severity"),
            "root_cause": analysis.get("root_cause"),
            "actions": analysis.get("actions"),
            "type": "AI_ALERT"
        }
        
        # Log critical alert
        self.critical(f"AI ALERT: {analysis.get('root_cause')}", alert)
        
        # Could send to monitoring service, Slack, etc.
        # await send_to_monitoring(alert)
    
    # Convenience methods that replace print()
    
    def debug(self, message: str, context: Dict = None):
        """Debug level log (replaces debug print statements)"""
        return self.log(LogLevel.DEBUG, message, context)
    
    def info(self, message: str, context: Dict = None):
        """Info level log (replaces standard print statements)"""
        return self.log(LogLevel.INFO, message, context)
    
    def warning(self, message: str, context: Dict = None):
        """Warning level log"""
        return self.log(LogLevel.WARNING, message, context)
    
    def error(self, message: str, context: Dict = None, exc_info: bool = True):
        """Error level log with exception info"""
        if exc_info:
            context = context or {}
            context["traceback"] = traceback.format_exc()
        return self.log(LogLevel.ERROR, message, context)
    
    def critical(self, message: str, context: Dict = None):
        """Critical level log"""
        return self.log(LogLevel.CRITICAL, message, context)
    
    async def analyze_performance(self) -> Dict:
        """Analyze system performance from logs"""
        
        # Calculate metrics from recent logs
        total_logs = len(self.recent_logs)
        if total_logs == 0:
            return {"status": "no_data"}
        
        error_rate = sum(1 for log in self.recent_logs if log.level == "ERROR") / total_logs
        warning_rate = sum(1 for log in self.recent_logs if log.level == "WARNING") / total_logs
        
        # Get AI insights
        prompt = f"""
        Analyze system performance based on:
        - Error rate: {error_rate:.2%}
        - Warning rate: {warning_rate:.2%}
        - Total logs: {total_logs}
        
        Provide performance assessment and recommendations.
        Format as JSON.
        """
        
        response = await self.llm.ainvoke(prompt)
        return json.loads(response.content)
    
    def get_logs(self, level: Optional[LogLevel] = None, limit: int = 100) -> List[LogEntry]:
        """Get recent logs, optionally filtered by level"""
        
        logs = list(self.recent_logs)
        
        if level:
            logs = [log for log in logs if log.level == level.name]
        
        return logs[-limit:]
    
    def clear_logs(self):
        """Clear log history (useful for testing)"""
        self.recent_logs.clear()
        self.error_context.clear()


# Global logger instance
logger = AILogger()


# Direct replacement functions for print()
def print_replacement(*args, **kwargs):
    """Direct replacement for print() function"""
    message = " ".join(str(arg) for arg in args)
    logger.info(message)


# Monkey-patch print if desired (use with caution!)
def replace_print_globally():
    """Replace Python's built-in print with AI logger"""
    import builtins
    builtins.print = print_replacement


# Convenience functions
def debug(message: str, **context):
    logger.debug(message, context)


def info(message: str, **context):
    logger.info(message, context)


def warning(message: str, **context):
    logger.warning(message, context)


def error(message: str, **context):
    logger.error(message, context)


def critical(message: str, **context):
    logger.critical(message, context)