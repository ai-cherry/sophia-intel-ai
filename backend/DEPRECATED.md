This directory contains legacy mirrors of API/service modules.

Status
- Deprecated in favor of the canonical `app/` package.
- New code and imports should target `app.*` modules.

Migration
- Update imports like `from backend.core.database` → `from app.api.core.database` (or `from app.core.*` when applicable).
- Routers: `from backend.routers.chat` → `from app.api.routers.chat`.

Removal Plan
- Identical mirrors will be removed in stages once references are switched.

