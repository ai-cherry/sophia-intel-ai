"""
JSON contracts for structured agent outputs.
These schemas enforce quality and consistency across agent responses.
"""

PLANNER_SCHEMA = """Return a JSON:
{ "milestones":[{"name":"","description":"","estimate_days":0,
  "epics":[{"name":"","stories":[
    {"id":"S-###","title":"","acceptance":["..."],"dependencies":["S-###"],"tags":["coding","debugging","qa","ux"]}
  ]}]}],
  "global_risks":["..."],
  "tool_hints":["..."],
  "success_metrics":["coverage≥90%","lighthouse≥90","p50≤200ms"] }"""

CRITIC_SCHEMA = """Return a JSON:
{ "verdict":"pass|revise",
  "findings":{"security":["..."],"data_integrity":["..."],"logic_correctness":["..."],"performance":["..."],"usability":["..."],"maintainability":["..."]},
  "must_fix":["S-###: minimal delta"], "nice_to_have":["..."], "minimal_patch_notes":"..." }"""

JUDGE_SCHEMA = """Return a JSON:
{ "decision":"accept|merge|reject", "selected":"A|B|C", "merged_spec":{},
  "rationale":["..."], "runner_instructions":["concrete steps, one per line"] }"""

GENERATOR_SCHEMA = """Return a JSON:
{ "approach":"","implementation_plan":["..."],"files_to_change":["..."],
  "test_plan":["..."],"estimated_loc":0,"risk_level":"low|medium|high" }"""