from __future__ import annotations
import asyncio
import psutil
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import threading


class MCPMonitor:
    """Background monitoring for MCP server and resources"""
    
    def __init__(self, stats_path: str = "./stats"):
        self.stats_path = Path(stats_path)
        self.stats_path.mkdir(parents=True, exist_ok=True)
        self.monitoring = True
        self.stats = {
            "memory": {},
            "cpu": {},
            "processes": {},
            "mcp_status": {},
            "indexing": {},
            "last_update": None
        }
        self._lock = threading.Lock()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent": memory.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_percent": swap.percent
        }
    
    def get_cpu_stats(self) -> Dict[str, Any]:
        """Get current CPU statistics"""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        
        return {
            "percent_per_core": cpu_percent,
            "percent_total": sum(cpu_percent) / len(cpu_percent),
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "freq_current": round(cpu_freq.current, 2) if cpu_freq else 0,
            "freq_max": round(cpu_freq.max, 2) if cpu_freq else 0
        }
    
    def get_process_stats(self) -> Dict[str, List[Dict]]:
        """Get statistics for MCP-related processes"""
        mcp_processes = []
        python_processes = []
        node_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent', 'cmdline']):
            try:
                info = proc.info
                cmdline = ' '.join(info.get('cmdline', [])) if info.get('cmdline') else info['name']
                
                proc_data = {
                    'pid': info['pid'],
                    'name': info['name'],
                    'memory_percent': round(info.get('memory_percent', 0), 2),
                    'cpu_percent': round(info.get('cpu_percent', 0), 2),
                    'command': cmdline[:100] + '...' if len(cmdline) > 100 else cmdline
                }
                
                # Categorize processes
                if 'mcp' in cmdline.lower() or 'modelcontextprotocol' in cmdline.lower():
                    mcp_processes.append(proc_data)
                elif 'python' in info['name'].lower() and ('uvicorn' in cmdline or 'mcp_server' in cmdline):
                    python_processes.append(proc_data)
                elif 'node' in info['name'].lower() and 'mcp' in cmdline.lower():
                    node_processes.append(proc_data)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "mcp": mcp_processes,
            "python": python_processes,
            "node": node_processes,
            "total_monitored": len(mcp_processes) + len(python_processes) + len(node_processes)
        }
    
    def check_mcp_server_health(self) -> Dict[str, Any]:
        """Check MCP server health"""
        import httpx
        
        health_status = {
            "api_server": "unknown",
            "vector_db": "unknown",
            "indexing": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check API server
        try:
            response = httpx.get("http://localhost:3333/healthz", timeout=2)
            if response.status_code == 200:
                health_status["api_server"] = "healthy"
                health_data = response.json()
                health_status["watch_enabled"] = health_data.get("watch", False)
                health_status["index_path"] = health_data.get("index", "")
            else:
                health_status["api_server"] = "unhealthy"
        except Exception:
            health_status["api_server"] = "offline"
        
        return health_status
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                with self._lock:
                    self.stats["memory"] = self.get_memory_stats()
                    self.stats["cpu"] = self.get_cpu_stats()
                    self.stats["processes"] = self.get_process_stats()
                    self.stats["mcp_status"] = self.check_mcp_server_health()
                    self.stats["last_update"] = datetime.now().isoformat()
                
                # Save stats to file
                stats_file = self.stats_path / "mcp_stats.json"
                with open(stats_file, 'w') as f:
                    json.dump(self.stats, f, indent=2)
                
                # Also save a history entry
                history_file = self.stats_path / f"history_{datetime.now().strftime('%Y%m%d')}.jsonl"
                with open(history_file, 'a') as f:
                    f.write(json.dumps(self.stats) + '\n')
                
            except Exception as e:
                print(f"Monitoring error: {e}")
            
            time.sleep(10)  # Update every 10 seconds
    
    def start(self):
        """Start monitoring in background thread"""
        thread = threading.Thread(target=self.monitor_loop, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current stats snapshot"""
        with self._lock:
            return self.stats.copy()


class BackgroundIndexer:
    """Background indexing service for repository files"""
    
    def __init__(self, repo_path: str, index_interval: int = 300):
        self.repo_path = Path(repo_path)
        self.index_interval = index_interval  # seconds
        self.indexing = True
        self.last_indexed = {}
        self.stats = {
            "total_files": 0,
            "indexed_files": 0,
            "pending_files": 0,
            "last_index_time": None,
            "index_duration_seconds": 0
        }
    
    async def index_repository(self):
        """Index or re-index the repository"""
        from dev_mcp_unified.indexing.chunker import ASTAwareChunker, iter_files
        from dev_mcp_unified.storage.vector_store import InMemoryVectorStore
        from dev_mcp_unified.embeddings.local_provider import LocalDeterministicEmbedding
        
        start_time = time.time()
        chunker = ASTAwareChunker()
        embedder = LocalDeterministicEmbedding(dims=256)
        store = InMemoryVectorStore(dims=256)
        
        indexed_count = 0
        total_files = 0
        
        for file_path in iter_files(str(self.repo_path)):
            total_files += 1
            
            # Check if file needs re-indexing
            stat = file_path.stat()
            mtime = stat.st_mtime
            
            if file_path in self.last_indexed and self.last_indexed[file_path] >= mtime:
                continue  # Skip unchanged files
            
            try:
                # Chunk the file
                chunks = chunker.chunk_file(file_path)
                
                # Generate embeddings for each chunk
                for chunk in chunks:
                    text = chunk['text']
                    embedding = embedder.embed_batch([text])[0]
                    
                    # Store in vector database
                    metadata = {
                        'file': str(file_path),
                        'type': chunk.get('type', 'unknown'),
                        'metadata': chunk.get('metadata', {})
                    }
                    store.add(embedding, metadata)
                
                self.last_indexed[file_path] = mtime
                indexed_count += 1
                
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")
        
        # Update stats
        self.stats.update({
            "total_files": total_files,
            "indexed_files": len(self.last_indexed),
            "pending_files": total_files - len(self.last_indexed),
            "last_index_time": datetime.now().isoformat(),
            "index_duration_seconds": round(time.time() - start_time, 2)
        })
        
        return indexed_count
    
    async def watch_loop(self):
        """Watch for changes and re-index periodically"""
        while self.indexing:
            try:
                indexed = await self.index_repository()
                if indexed > 0:
                    print(f"Indexed {indexed} files")
            except Exception as e:
                print(f"Indexing error: {e}")
            
            await asyncio.sleep(self.index_interval)
    
    def start(self):
        """Start background indexing"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.watch_loop())
    
    def stop(self):
        """Stop indexing"""
        self.indexing = False


def start_monitoring(repo_path: str = ".", stats_path: str = "./stats"):
    """Start all monitoring and indexing services"""
    
    # Start resource monitor
    monitor = MCPMonitor(stats_path=stats_path)
    monitor_thread = monitor.start()
    print("✅ Resource monitoring started")
    
    # Start background indexer
    indexer = BackgroundIndexer(repo_path=repo_path)
    indexer_thread = threading.Thread(target=indexer.start, daemon=True)
    indexer_thread.start()
    print("✅ Background indexing started")
    
    print(f"📊 Stats available at: {Path(stats_path).absolute()}/mcp_stats.json")
    print("🔍 Monitoring MCP processes...")
    
    return monitor, indexer


if __name__ == "__main__":
    import sys
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    monitor, indexer = start_monitoring(repo_path)
    
    try:
        while True:
            time.sleep(60)
            stats = monitor.get_current_stats()
            print(f"\n📊 Current Stats:")
            print(f"  Memory: {stats['memory'].get('percent', 0):.1f}% used")
            print(f"  CPU: {stats['cpu'].get('percent_total', 0):.1f}% used")
            print(f"  Processes: {stats['processes'].get('total_monitored', 0)} monitored")
            print(f"  MCP Server: {stats['mcp_status'].get('api_server', 'unknown')}")
    except KeyboardInterrupt:
        print("\n⏹️ Stopping monitoring...")
        monitor.stop()
        indexer.stop()