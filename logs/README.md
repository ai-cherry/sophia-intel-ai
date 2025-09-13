This directory ignores raw runtime logs but allows lightweight summaries to be committed.

Rules:
- Do not commit raw logs or PII.
- Summaries only: use `*.summary.*` or Markdown `*.md`.
- Rotate and aggregate logs outside the repo; include small summaries here if needed for audits.

