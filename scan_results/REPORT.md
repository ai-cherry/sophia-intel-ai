# SOPHIA-INTEL-AI REPOSITORY SCAN REPORT

## Statistics
- Duplicate basenames:        0
- Suspicious imports:        2
- TODO/FIXME/etc:      125
- Empty/stub files:       44
- Potential secrets (top 200):      200
- Bare excepts:      192
- TSX raw '< number' instances:        0

## Critical (first 5)
tests/integration/test_mcp_servers_integration.py:25:    from artemis.orchestrator import ArtemisSwarmOrchestrator
tests/integration/test_artemis_iac_integration.py:17:from artemis.orchestrator.core_orchestrator import ArtemisOrchestrator

## Security (first 5)
agent-ui/src/hooks/useServiceConfig.ts:69:    max_tokens_per_request: number;
agent-ui/src/hooks/useServiceConfig.ts:216:            max_tokens_per_request: 4096,
agent-ui/src/hooks/useModelRegistry.ts:18:  cost_per_1k_tokens: number;
agent-ui/src/hooks/useModelRegistry.ts:26:  max_tokens: number;
agent-ui/src/hooks/useModelRegistry.ts:36:  token_usage: Record<string, number>;

## TODOs (first 10)
agent-ui/src/components/dev/MetricsDebugPanel.tsx:10:    const flag = process.env.NEXT_PUBLIC_SHOW_METRICS_DEBUG;
pulumi_esc_manager.py:524:                        else "DEBUG"
config/manager.py:174:            "DEBUG": "debug",
infrastructure/pulumi/production/esc_config.py:262:                    "log_level": "DEBUG",
infrastructure/pulumi/esc/audit_logger.py:27:    DEBUG = "debug"
app/factory/agent_catalog.py:120:                AgentCapability.DEBUGGING,
agent-ui/src/components/playground/ChatArea/Messages/Multimedia/Audios/Audios.tsx:55:      // TODO :: find a better way to handle the key
app/factory/models.py:34:    DEBUGGING = "debugging"
automation/scripts/config-manager.py:490:        logging.getLogger().setLevel(logging.DEBUG)
agent-ui/src/app/(sophia)/chat/page.tsx:175:        // TODO: Send to speech-to-text endpoint
