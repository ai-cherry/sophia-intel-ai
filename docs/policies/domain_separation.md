# Domain Separation Policy (Sophia vs Builder)

Purpose
- Preserve strict boundaries between Business Intelligence (Sophia) and Coding/Repo operations (Builder).

Rules
- API: The Sophia API must not mount Builder routers. Builder coding flows run via CLI agents/swarms only.
- UI: `sophia-intel-app/` and `builder-agno-system/` are independent apps with no cross-imports.
- Data/Auth: Separate JWT audiences, CORS, Redis prefixes, and DB schemas per domain.

Enforcement
- CI “domain wall” guard runs in strict mode; import-linter/ESLint forbid cross-imports.
- PR template requires scope declaration (Sophia or Builder) and confirmation of this policy.

Exceptions
- Any cross-domain change requires explicit ADR and dual approval.

