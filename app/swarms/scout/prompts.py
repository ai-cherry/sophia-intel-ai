SCOUT_OUTPUT_SCHEMA = """
Sections:
- FINDINGS: bullet points of discovered issues/patterns
- INTEGRATIONS: list of subsystems and their interactions
- RISKS: potential failures, security concerns, bottlenecks
- RECOMMENDATIONS: prioritized, actionable steps
- METRICS: context hits, files scanned, time, tokens
- CONFIDENCE: 0.0-1.0
"""

ANALYST_OVERLAY = """
Use heuristics: hotspots (complexity+churn), duplication, dead code, security smells.
Reference memory_context.relevant_documents where applicable.
Emit sections per SCOUT_OUTPUT_SCHEMA.
"""

STRATEGIST_OVERLAY = """
Map integrations: data flow, MCP wiring, external services.
Identify cross-cutting concerns and failure domains.
Emit sections per SCOUT_OUTPUT_SCHEMA.
"""

VALIDATOR_OVERLAY = """
Validate feasibility, constraints, and risks.
Add targeted test suggestions.
Emit sections per SCOUT_OUTPUT_SCHEMA.
"""
