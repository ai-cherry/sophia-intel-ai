import time, json, sys, os
from pathlib import Path
from typing import Dict, Any
from collections import defaultdict, deque
from datetime import datetime

LOG_FILE = Path(os.getenv("SWARM_LOG_FILE", ".swarm_handoffs.log"))
METRICS_FILE = Path(os.getenv("SWARM_METRICS_FILE", ".swarm_metrics.json"))
MAX_LOG_SIZE = int(os.getenv("MAX_LOG_SIZE_MB", "50")) * 1024 * 1024

class SwarmTelemetry:
    def __init__(self):
        self.agent_stats = defaultdict(lambda: {
            "calls": 0, "total_time": 0, "avg_time": 0,
            "output_chars": 0, "errors": 0, "last_seen": 0
        })
        self.recent_events = deque(maxlen=100)
        self.start_time = time.time()
        
    def log_event(self, event: Dict[str, Any]) -> None:
        """Log event with timestamp and structured format"""
        event["timestamp"] = time.time()
        event["iso_time"] = datetime.fromtimestamp(event["timestamp"]).isoformat()
        
        # Rotate log if too large
        if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
            self._rotate_log()
        
        # Append to log
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(event) + "\n")
        
        # Update metrics
        self._update_metrics(event)
        self.recent_events.append(event)
    
    def _rotate_log(self) -> None:
        """Rotate log file when it gets too large"""
        if LOG_FILE.exists():
            backup_path = LOG_FILE.with_suffix(f".log.{int(time.time())}")
            LOG_FILE.rename(backup_path)
            print(f"Rotated log to {backup_path}")
    
    def _update_metrics(self, event: Dict[str, Any]) -> None:
        """Update agent performance metrics"""
        agent = event.get("agent", "unknown")
        stats = self.agent_stats[agent]
        
        stats["calls"] += 1
        stats["last_seen"] = event["timestamp"]
        
        if "len" in event:
            stats["output_chars"] += event["len"]
        
        if "duration" in event:
            stats["total_time"] += event["duration"]
            stats["avg_time"] = stats["total_time"] / stats["calls"]
        
        if event.get("event") == "error":
            stats["errors"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        uptime = time.time() - self.start_time
        
        return {
            "uptime_seconds": uptime,
            "total_events": sum(stats["calls"] for stats in self.agent_stats.values()),
            "total_errors": sum(stats["errors"] for stats in self.agent_stats.values()),
            "agents": dict(self.agent_stats),
            "recent_activity": list(self.recent_events)[-10:],
            "timestamp": time.time()
        }
    
    def save_metrics(self) -> None:
        """Save metrics to file"""
        with METRICS_FILE.open("w") as f:
            json.dump(self.get_metrics(), f, indent=2)

# Global telemetry instance
telemetry = SwarmTelemetry()

def log(event: Dict[str, Any]) -> None:
    """Public interface for logging events"""
    telemetry.log_event(event)

def tail_with_analysis():
    """Tail log with live metrics and analysis"""
    print(f"Monitoring {LOG_FILE} (Press Ctrl+C to stop)")
    print("=" * 60)
    
    last_size = LOG_FILE.stat().st_size if LOG_FILE.exists() else 0
    
    while True:
        try:
            time.sleep(1)
            
            if not LOG_FILE.exists():
                continue
                
            current_size = LOG_FILE.stat().st_size
            if current_size <= last_size:
                continue
            
            # Read new content
            with LOG_FILE.open() as f:
                f.seek(last_size)
                new_content = f.read()
            
            # Process new events
            for line in new_content.strip().split('\n'):
                if not line:
                    continue
                    
                try:
                    event = json.loads(line)
                    telemetry._update_metrics(event)
                    
                    # Display formatted event
                    agent = event.get("agent", "system")
                    timestamp = datetime.fromtimestamp(event.get("timestamp", time.time()))
                    event_type = event.get("event", "unknown")
                    
                    if event_type == "output":
                        char_count = event.get("len", 0)
                        print(f"[{timestamp.strftime('%H:%M:%S')}] {agent:12} → {char_count:6} chars")
                    elif event_type == "error":
                        error_msg = event.get("error", "unknown error")
                        print(f"[{timestamp.strftime('%H:%M:%S')}] {agent:12} ✗ {error_msg}")
                    else:
                        print(f"[{timestamp.strftime('%H:%M:%S')}] {agent:12} • {event_type}")
                        
                except json.JSONDecodeError:
                    continue
            
            last_size = current_size
            
            # Periodic metrics display (every 30 seconds)
            if int(time.time()) % 30 == 0:
                metrics = telemetry.get_metrics()
                print("\n" + "=" * 60)
                print(f"METRICS (Uptime: {metrics['uptime_seconds']:.0f}s)")
                print("-" * 60)
                for agent, stats in metrics["agents"].items():
                    avg_time = stats.get("avg_time", 0)
                    error_rate = stats["errors"] / max(1, stats["calls"]) * 100
                    print(f"{agent:12} {stats['calls']:4} calls, {stats['output_chars']:8} chars, {error_rate:5.1f}% errors")
                print("=" * 60 + "\n")
                
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            telemetry.save_metrics()
            print(f"Final metrics saved to {METRICS_FILE}")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--metrics":
        print(json.dumps(telemetry.get_metrics(), indent=2))
    else:
        tail_with_analysis()