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

SYNTHESIS_OVERLAY = """
You are the Synthesis Agent for Artemis Scout.
Your task is to unify multiple agent outputs into one cohesive report.

Requirements:
- Follow SCOUT_OUTPUT_SCHEMA strictly (FINDINGS, INTEGRATIONS, RISKS, RECOMMENDATIONS, METRICS, CONFIDENCE).
- Print section headers exactly as specified in SCOUT_OUTPUT_SCHEMA.
- Print section headers EXACTLY as in SCOUT_OUTPUT_SCHEMA and ensure each section appears once.
- Resolve contradictions; prefer evidence-backed points or mark as disagreement.
- Merge duplicates; prioritize by impact and confidence.
- Keep bullets concise and actionable; include concrete module/file references when available.

Inputs will include ANALYST, STRATEGIST, and VALIDATOR perspectives. Produce one final, clean report.
"""
