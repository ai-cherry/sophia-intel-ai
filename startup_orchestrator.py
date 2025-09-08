#!/usr/bin/env python3
#!/usr/bin/env python3
"""Sophia AI Unified Startup Orchestrator

Combines dependency-aware service management with rich health checks.
"""

import asyncio
import contextlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict

import aiohttp
import httpx
import psutil
import redis
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceOrchestrator:
    """Manage service startup with dependency resolution and health checks."""

    def __init__(self, config_path: str = "startup-config.yml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.services: Dict[str, Dict] = {}
        self.startup_order = list(self.config.get("services", {}).keys())

    def _load_config(self) -> Dict:
        try:
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {"services": {}}
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return {"services": {}}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            return {"services": {}}

    async def start_service(self, name: str, cfg: Dict) -> bool:
        logger.info(f"Starting service: {name}")
        if await self._is_service_healthy(name, cfg):
            logger.info(f"Service {name} already running")
            self.services[name] = {"status": "running", "process": None}
            return True

        process = None
        cmd = cfg.get("command")
        if cmd:
            env = {**os.environ, **cfg.get("environment", {})}
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cfg.get("working_dir", "/workspace"),
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.sleep(cfg.get("startup_delay", 0))

        timeout = cfg.get("timeout", 30)
        start = time.time()
        while time.time() - start < timeout:
            if await self._is_service_healthy(name, cfg):
                self.services[name] = {"status": "running", "process": process}
                return True
            await asyncio.sleep(2)

        if process:
            process.terminate()
        self.services[name] = {"status": "failed", "process": process}
        logger.error(f"Service {name} failed to start")
        return False

    async def _is_service_healthy(self, name: str, cfg: Dict) -> bool:
        health = cfg.get("health_check")
        if not health:
            return True
        try:
            if name == "redis":
                r = redis.Redis(host="localhost", port=6379, decode_responses=True)
                return r.ping()
            if name == "api":
                resp = httpx.get("http://localhost:8000/health", timeout=5)
                return resp.status_code == 200
            if name == "dashboard":
                resp = httpx.get("http://localhost:8501/_stcore/health", timeout=5)
                return resp.status_code == 200
            if name == "grafana":
                resp = httpx.get("http://localhost:3001/api/health", timeout=5)
                return resp.status_code == 200
            if name == "prometheus":
                resp = httpx.get("http://104.171.202.103:9090/-/healthy", timeout=5)
                return resp.status_code == 200
            if isinstance(health, str) and health.startswith("http"):
                async with aiohttp.ClientSession() as session:
                    async with session.get(health, timeout=5) as r:
                        return r.status == 200
        except Exception as e:
            logger.debug(f"Health check failed for {name}: {e}")
            return False
        return False

    async def start_all(self) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for name in self.startup_order:
            cfg = self.config["services"].get(name, {})
            deps = cfg.get("dependencies", [])
            if any(not results.get(dep, False) for dep in deps):
                logger.error(f"Dependencies for {name} not satisfied: {deps}")
                results[name] = False
                continue
            results[name] = await self.start_service(name, cfg)
        return results

    async def stop_all(self) -> None:
        for name in reversed(self.startup_order):
            svc = self.services.get(name)
            if svc and svc.get("process"):
                proc = svc["process"]
                proc.terminate()
                with contextlib.suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(proc.wait(), timeout=10)
            if svc:
                svc["status"] = "stopped"

    def get_status(self) -> Dict[str, str]:
        return {n: s.get("status", "unknown") for n, s in self.services.items()}

    def get_system_info(self) -> Dict[str, float]:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Sophia AI Service Orchestrator")
    parser.add_argument("--config", default="startup-config.yml", help="Path to config file")
    parser.add_argument("--start", action="store_true", help="Start all services")
    parser.add_argument("--stop", action="store_true", help="Stop all services")
    parser.add_argument("--status", action="store_true", help="Show status and system info")
    args = parser.parse_args()

    orchestrator = ServiceOrchestrator(args.config)

    if args.start:
        results = await orchestrator.start_all()
        print(json.dumps(results, indent=2))
    elif args.stop:
        await orchestrator.stop_all()
    elif args.status:
        info = {
            "services": orchestrator.get_status(),
            "system": orchestrator.get_system_info(),
            "timestamp": time.time(),
        }
        print(json.dumps(info, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
