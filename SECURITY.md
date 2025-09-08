# Security Policy and Dependency Notes

Date: 2025-09-04

Summary of changes

- Replaced python-jose (which depends on ecdsa) with PyJWT across the project to eliminate an unfixed side-channel timing advisory on ecdsa (GHSA-wj6h-64fc-37mp / CVE-2024-23342).
- Updated manifests and lockfiles using uv for reproducible builds.

Rationale

- ecdsa library has a known timing side-channel on P-256 affecting signing operations. The upstream ecdsa project treats side-channel resistance as out-of-scope, and no fix is planned.
- PyJWT uses cryptography for algorithms like HS*, RS*, and ES\* and does not depend on the ecdsa package, avoiding the advisory.

Scope of changes

- Code: app/api/auth.py updated to use PyJWT (import jwt) and catch jwt.PyJWTError.
- Dependencies:
  - requirements.txt: python-jose[cryptography] → PyJWT==2.9.0
  - app/requirements.txt: added PyJWT==2.9.0
  - requirements-2025.txt: python-jose[cryptography] → PyJWT>=2.8.0
- Lockfiles regenerated with uv:
  - requirements.lock
  - app/requirements.lock
  - requirements-2025.lock

Operational guidance

- Installing dependencies (examples, system Python; no in-repo venvs):
  - uv pip sync -r requirements.lock
  - or: pip3 install -r requirements.txt

Compatibility notes

- PyJWT API:
  - Encode: jwt.encode(payload, key, algorithm="HS256")
  - Decode: jwt.decode(token, key, algorithms=["HS256"])
  - Exceptions: jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.PyJWTError
- Existing modules already using import jwt (PyJWT) required no change; only modules using from jose import ... were updated.

Verification

- pip-audit and safety show no vulnerabilities stemming from ecdsa after the change.
- Unit/integration tests that rely on jwt should continue to pass; tests using import jwt were already PyJWT-based.

Contact

- For questions about this change, open an issue or contact the maintainers.
