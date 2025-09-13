from __future__ import annotations

import asyncio
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException

from app.integrations.registry import registry
from app.core.metrics import inc_counter
from app.core.db import session_scope
from sqlalchemy import text
import hashlib
import json
from datetime import datetime


router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/catalog")
async def catalog():
    enabled = registry.enabled()
    return {
        "integrations": [
            {"name": info.name, "enabled": info.enabled, "details": info.details}
            for info in enabled.values()
        ]
    }


@router.get("/health")
async def health():
    tasks = []
    results: Dict[str, Dict] = {}
    for name, info in registry.enabled().items():
        if not info.enabled:
            results[name] = {"ok": False, "details": {"enabled": False}}
            continue
        client = registry.get(name)
        tasks.append((name, asyncio.create_task(client.health())))
    for name, task in tasks:
        try:
            res = await task
            results[name] = res
            inc_counter("integrations_health_total", label=f"{name}:ok")
        except Exception as e:
            results[name] = {"ok": False, "details": {"error": str(e)}}
            inc_counter("integrations_health_total", label=f"{name}:error")
    return results


@router.post("/{name}/sync")
async def sync_integration(name: str):
    client = registry.get(name)
    if not client:
        raise HTTPException(status_code=404, detail=f"Integration {name} not enabled or unknown")
    try:
        # Fetch a page of entities
        data = await client.list_entities(limit=25)
        items = data.get("items", [])
        count = len(items)

        # Attempt to write to landing zone if DB configured
        try:
            async with session_scope() as session:
                # Create sync run
                res = await session.execute(
                    text(
                        "INSERT INTO sync_runs (source_system, started_at, status) "
                        "VALUES (:src, NOW(), 'running') RETURNING id"
                    ),
                    {"src": name},
                )
                run_id = res.scalar_one()
                # Insert items with checksum and upsert-like behavior via unique index
                inserted = 0
                for it in items:
                    payload = json.dumps(it, default=str)
                    checksum = hashlib.md5(payload.encode()).hexdigest()
                    external_id: Optional[str] = None
                    obj_type: Optional[str] = None
                    if isinstance(it, dict):
                        external_id = str(it.get("id") or it.get("external_id") or "") or None
                        obj_type = str(it.get("object") or it.get("type") or "record")
                    try:
                        await session.execute(
                            text(
                                "INSERT INTO ingestion_raw (source_system, object_type, external_id, payload, checksum, ingested_at, sync_run_id) "
                                "VALUES (:src, :otype, :eid, :payload::jsonb, :ck, NOW(), :rid)"
                            ),
                            {
                                "src": name,
                                "otype": obj_type,
                                "eid": external_id,
                                "payload": payload,
                                "ck": checksum,
                                "rid": run_id,
                            },
                        )
                        inserted += 1
                    except Exception:
                        # Likely duplicate due to unique index; ignore
                        pass
                # Mark run complete
                await session.execute(
                    text(
                        "UPDATE sync_runs SET completed_at = NOW(), status = 'completed', stats = stats || :stats::jsonb WHERE id = :rid"
                    ),
                    {
                        "rid": run_id,
                        "stats": json.dumps({"attempted": count, "inserted": inserted}),
                    },
                )
                await session.commit()
        except Exception:
            # No DB configured or error writing; continue returning the count
            pass
        inc_counter("integrations_sync_total", label=f"{name}:ok")
        return {"synced": count, "next": data.get("next")}
    except Exception as e:
        inc_counter("integrations_sync_total", label=f"{name}:error")
        raise HTTPException(status_code=500, detail=str(e))
