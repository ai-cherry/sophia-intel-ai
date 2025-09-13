# Evals

Purpose: Curated evaluation sets and runners for accuracy, latency, and grounding budgets.

Structure
- golden_qa/ — regression Q&A cases (JSON/CSV/MD acceptable)
- accuracy/ — task-specific accuracy tests
- grounding_budgets/ — expected token/latency budgets per task

Conventions
- Keep small, versioned artifacts; large datasets belong outside the repo.
- Add a `README.md` per subfolder explaining format and how to run.

