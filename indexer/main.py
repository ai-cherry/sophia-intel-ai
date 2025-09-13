from __future__ import annotations
import asyncio
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List
try:
    import weaviate
except Exception as e:  # pragma: no cover
    weaviate = None
SCAN_EXTS = {".py", ".md", ".txt", ".json", ".yml", ".yaml"}
IGNORE_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build"}
CLASS_NAME = "CodeFile"
@dataclass
class Repo:
    name: str
    path: Path
def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in SCAN_EXTS:
            yield p
async def run() -> None:
    weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    repos = [
        Repo("sophia", Path(os.getenv("SOPHIA_PATH", "/workspace/sophia"))),
        Repo("", Path(os.getenv("_PATH", "/workspace/"))),
    ]
    if weaviate is None:
        print("weaviate-client not installed; exiting")
        return
    client = weaviate.connect_to_local(
        host=weaviate_url.replace("http://", "").replace("https://", "")
    )
    try:
        # Ensure class exists (non-vectorized)
        if CLASS_NAME not in client.collections.list_all():
            client.collections.create(
                CLASS_NAME,
                vectorizer_config=weaviate.classes.config.Configure.Vectorizer.none(),
                properties=[
                    weaviate.classes.config.Property(
                        name="repo", data_type=weaviate.classes.config.DataType.TEXT
                    ),
                    weaviate.classes.config.Property(
                        name="file_path",
                        data_type=weaviate.classes.config.DataType.TEXT,
                    ),
                    weaviate.classes.config.Property(
                        name="content", data_type=weaviate.classes.config.DataType.TEXT
                    ),
                    weaviate.classes.config.Property(
                        name="mtime", data_type=weaviate.classes.config.DataType.NUMBER
                    ),
                    weaviate.classes.config.Property(
                        name="size", data_type=weaviate.classes.config.DataType.NUMBER
                    ),
                ],
            )
        coll = client.collections.get(CLASS_NAME)
        cache: Dict[str, float] = {}
        scan_interval = int(os.getenv("INDEX_SCAN_INTERVAL", "15"))
        while True:
            for repo in repos:
                if not repo.path.exists():
                    continue
                for f in iter_files(repo.path):
                    rel = f.relative_to(repo.path)
                    key = f"{repo.name}:{rel}"
                    mtime = f.stat().st_mtime
                    if cache.get(key, 0) >= mtime:
                        continue
                    try:
                        content = f.read_text(errors="ignore")
                    except Exception:
                        continue
                    cache[key] = mtime
                    coll.data.insert(
                        {
                            "repo": repo.name,
                            "file_path": str(rel),
                            "content": content,
                            "mtime": mtime,
                            "size": len(content),
                        }
                    )
            await asyncio.sleep(scan_interval)
    finally:
        client.close()
if __name__ == "__main__":
    asyncio.run(run())
