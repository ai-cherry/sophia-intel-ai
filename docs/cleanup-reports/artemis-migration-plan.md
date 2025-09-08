# Artemis Migration Plan (Draft)

The following files in this repo appear to belong in the ai-cherry/artemis-cli repository.
Migrate them to maintain a clean boundary between core (Sophia) and Artemis app.

## Candidate Files to Move
- app/artemis/__pycache__/agent_factory.cpython-312.pyc
- app/artemis/__pycache__/agent_factory.cpython-313.pyc
- app/artemis/__pycache__/artemis_orchestrator.cpython-312.pyc
- app/artemis/__pycache__/artemis_orchestrator.cpython-313.pyc
- app/artemis/__pycache__/artemis_semantic_orchestrator.cpython-312.pyc
- app/artemis/__pycache__/artemis_semantic_orchestrator.cpython-313.pyc
- app/artemis/__pycache__/portkey_unified_factory.cpython-312.pyc
- app/artemis/__pycache__/portkey_unified_factory.cpython-313.pyc
- app/artemis/__pycache__/unified_factory.cpython-312.pyc
- app/artemis/__pycache__/unified_factory.cpython-313.pyc
- app/artemis/agent_factory.py
- app/artemis/artemis_orchestrator.py
- app/artemis/artemis_semantic_orchestrator.py
- app/artemis/factories/__init__.py
- app/artemis/factories/__pycache__/__init__.cpython-312.pyc
- app/artemis/factories/__pycache__/agent_factory.cpython-312.pyc
- app/artemis/factories/agent_factory.py
- app/artemis/factories/base_factory.py
- app/artemis/portkey_unified_factory.py
- app/artemis/scout_swarm/__pycache__/ultimate_scout_swarm.cpython-312.pyc
- app/artemis/scout_swarm/__pycache__/ultimate_scout_swarm.cpython-313.pyc
- app/artemis/scout_swarm/ultimate_scout_swarm.py
- app/artemis/ui/command_center.html
- app/artemis/unified_factory.py
- artemis_connectivity_test_20250905_152106.json
- artemis_connectivity_test_20250905_152145.json
- artemis_final_20250906_070901.json
- artemis_monitor_initial_20250905_152923.json
- artemis_parallel_20250906_064311.json
- artemis_parallel_20250906_073755.json
- artemis_parallel_20250906_074304.json
- artemis_parallel_20250906_074600.json
- artemis_parallel_20250906_074644.json
- artemis_real_scan_20250906_080350.json
- artemis_real_scan_20250906_080512.json
- artemis_real_scan_20250906_081012.json
- artemis_scan_20250906_063436.json
- artemis_server_standalone.py
- artemis_tactical_report_20250905_142045.json
- artemis_tactical_report_20250905_151014.json
- artemis_working_20250906_070625.json
- bin/artemis-run
- test_gong_integration_with_artemis.py

## Suggested Destination
- In artemis-cli under matching paths (e.g., app/artemis/...)
- Add Dockerfiles/compose in artemis-cli for Artemis servers and CLI

## Post-Migration Tasks
- Remove these files from sophia-intel-ai
- Update compose integration to use ARTEMIS_PATH or remote service endpoints
- Add CI guardrails to block new app/artemis/* in this repo
