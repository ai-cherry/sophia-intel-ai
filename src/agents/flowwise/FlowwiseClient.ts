import type { AgentDefinition, FlowwiseFactorySummary } from '../../lib/dashboardTypes';

const FACTORY_ENDPOINT = '/api/flowwise/factories';
const FLOWWISE_AGENT_PREFIX = /^FLW_[A-Z]{2,}_[A-Z0-9_]+$/;

export class FlowwiseClient {
  async listFactories(): Promise<FlowwiseFactorySummary[]> {
    const response = await fetch(FACTORY_ENDPOINT);

    if (!response.ok) {
      throw new Error(`Unable to load Flowwise factories (${response.status})`);
    }

    const payload = (await response.json()) as FlowwiseFactorySummary[];
    payload.forEach((factory) => {
      factory.flows.forEach((flow) => this.assertCanonicalName(flow));
    });

    return payload;
  }

  private assertCanonicalName(agent: AgentDefinition) {
    if (!FLOWWISE_AGENT_PREFIX.test(agent.id)) {
      throw new Error(`Flowwise agent ${agent.id} violates canonical naming`);
    }
  }
}

export default new FlowwiseClient();
