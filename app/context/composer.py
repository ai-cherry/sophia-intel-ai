from __future__ import annotations

import os
from typing import Any, Dict, Optional

from app.integrations.registry import registry
from app.core.cache import get_redis
import json


class ContextComposer:
    """Assemble lightweight context bundles from integrations.

    Keep it minimal: fetch a few items per integration and prepare a compact JSON
    safe to include in prompts or dashboard widgets.
    """

    async def person(self, email: str) -> Dict[str, Any]:
        # Cache lookup
        rc = await get_redis()
        cache_key = f"context:person:{email.lower()}"
        if rc is not None:
            cached = await rc.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except Exception:
                    pass
        bundle: Dict[str, Any] = {"type": "person", "key": email, "sections": []}

        # Lattice profile (if enabled)
        if registry.get("lattice"):
            bundle["sections"].append({"source": "lattice", "summary": f"Profile for {email}"})

        # Asana tasks summary
        if registry.get("asana"):
            bundle["sections"].append({"source": "asana", "summary": "Top 3 tasks (placeholder)"})

        # Linear tasks summary
        if registry.get("linear"):
            bundle["sections"].append({"source": "linear", "summary": "Top 3 issues (placeholder)"})

        # Slack presence (placeholder)
        if registry.get("slack"):
            bundle["sections"].append({"source": "slack", "summary": "Presence unknown (placeholder)"})

        # Gong calls
        if registry.get("gong"):
            bundle["sections"].append({"source": "gong", "summary": "Recent calls (placeholder)"})

        # Intercom conversations
        if registry.get("intercom"):
            bundle["sections"].append({"source": "intercom", "summary": "Recent conversations (placeholder)"})

        if rc is not None:
            try:
                await rc.setex(cache_key, 600, json.dumps(bundle))  # 10 min TTL
            except Exception:
                pass
        return bundle

    async def company(self, domain: str) -> Dict[str, Any]:
        rc = await get_redis()
        cache_key = f"context:company:{domain.lower()}"
        if rc is not None:
            cached = await rc.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except Exception:
                    pass
        bundle: Dict[str, Any] = {"type": "company", "key": domain, "sections": []}

        if registry.get("salesforce"):
            bundle["sections"].append({"source": "salesforce", "summary": f"Account snapshot for {domain} (placeholder)"})

        if registry.get("hubspot"):
            bundle["sections"].append({"source": "hubspot", "summary": "Deals/contacts (placeholder)"})

        if registry.get("airtable"):
            bundle["sections"].append({"source": "airtable", "summary": "OKRs / curated info (placeholder)"})

        if registry.get("intercom"):
            bundle["sections"].append({"source": "intercom", "summary": "Conversations (placeholder)"})

        if registry.get("gong"):
            bundle["sections"].append({"source": "gong", "summary": "Recent calls (placeholder)"})

        if rc is not None:
            try:
                await rc.setex(cache_key, 600, json.dumps(bundle))
            except Exception:
                pass
        return bundle
