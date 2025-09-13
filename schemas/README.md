# Schemas

Goal: Centralize domain schemas (entities, facts, episodes) and ontology.

Structure
- domain/entities/ — core entities
- domain/facts/ — fact records and metrics
- domain/episodes/ — episodic records
- domain/ontology.yml — relationships and types
- adapters/ — adapter-specific projections (e.g., Weaviate, Qdrant)

Notes
- Existing adapter schemas remain under `schemas/weaviate/` for now. Migrate incrementally.
- Validate changes via CI before moving adapter files.

