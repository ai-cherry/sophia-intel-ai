import os
from unittest.mock import patch


async def test_delta_index_synthetic(tmp_path):
    # Create synthetic files
    repo = tmp_path
    (repo / "a.py").write_text("print('a')\n")
    (repo / "README.md").write_text("hello\n")

    # Fake MCP client that uses local fs
    class Fake:
        def repo_index(self, root=".", max_bytes_per_file=50000):
            files = []
            for p in repo.rglob("*"):
                if p.is_file():
                    files.append(
                        {"path": str(p.relative_to(repo)), "bytes": p.stat().st_size}
                    )
            return {"files": files}

        def fs_read(self, path, max_bytes=50000):
            p = repo / path
            return {"content": p.read_text()[:max_bytes]}

    # Patch StdioMCPClient and memory router to no-op
    with patch("app.swarms.scout.delta_index.StdioMCPClient", return_value=Fake()):

        async def fake_upsert(chunks, domain):
            return type(
                "Rep",
                (),
                {"chunks_stored": len(chunks), "chunks_processed": len(chunks)},
            )()

        with patch("app.swarms.scout.delta_index.get_memory_router") as gmr:
            gmr.return_value = type("R", (), {"upsert_chunks": fake_upsert})()
            os.environ["SCOUT_DELTA_INDEX_ENABLED"] = "true"
            from app.swarms.scout.delta_index import delta_index

            rep = await delta_index(repo_root=str(repo))
            assert rep["ok"] is True
            assert rep["upserted"] >= 1
