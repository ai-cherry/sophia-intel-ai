import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Dict


@dataclass
class Job:
    id: str
    kind: str
    payload: Dict[str, Any]
    status: str = "queued"
    log: list[str] = field(default_factory=list)


class JobQueue:
    def __init__(self, workers: int = 2):
        self.q: asyncio.Queue[Job] = asyncio.Queue()
        self.jobs: Dict[str, Job] = {}
        self.handlers: Dict[str, Callable[[Job], Any]] = {}
        self.workers = workers
        self._tasks: list[asyncio.Task] = []

    def register(self, kind: str, handler: Callable[[Job], Any]):
        self.handlers[kind] = handler

    async def start(self):
        for _ in range(self.workers):
            self._tasks.append(asyncio.create_task(self._worker()))

    async def stop(self):
        for t in self._tasks:
            t.cancel()

    async def enqueue(self, job: Job):
        self.jobs[job.id] = job
        await self.q.put(job)

    async def _worker(self):
        while True:
            job = await self.q.get()
            job.status = "running"
            try:
                handler = self.handlers.get(job.kind)
                if not handler:
                    job.log.append(f"no handler for {job.kind}")
                    job.status = "failed"
                else:
                    handler(job)
                    job.status = "completed"
            except Exception as e:
                job.log.append(str(e))
                job.status = "failed"
            finally:
                self.q.task_done()

