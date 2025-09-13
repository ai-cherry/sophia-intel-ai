from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.context.composer import ContextComposer
from app.core.metrics import inc_counter
import time


router = APIRouter(prefix="/api/context", tags=["context"])
composer = ContextComposer()


@router.get("/person")
async def person_context(email: str = Query(..., min_length=3)):
    try:
        start = time.perf_counter()
        bundle = await composer.person(email)
        dur = time.perf_counter() - start
        inc_counter("context_requests_total", label="person:ok")
        # Latency buckets (rough)
        b = "lt100ms" if dur < 0.1 else "lt300ms" if dur < 0.3 else "lt1s" if dur < 1.0 else "gte1s"
        inc_counter("context_latency_bucket", label=f"person:{b}")
        return bundle
    except Exception as e:
        inc_counter("context_requests_total", label="person:error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company")
async def company_context(domain: str = Query(..., min_length=3)):
    try:
        start = time.perf_counter()
        bundle = await composer.company(domain)
        dur = time.perf_counter() - start
        inc_counter("context_requests_total", label="company:ok")
        b = "lt100ms" if dur < 0.1 else "lt300ms" if dur < 0.3 else "lt1s" if dur < 1.0 else "gte1s"
        inc_counter("context_latency_bucket", label=f"company:{b}")
        return bundle
    except Exception as e:
        inc_counter("context_requests_total", label="company:error")
        raise HTTPException(status_code=500, detail=str(e))
