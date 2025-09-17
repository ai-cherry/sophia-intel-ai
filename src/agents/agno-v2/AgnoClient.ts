import type { AgentDefinition, AgnoWorkspaceSummary } from '../../lib/dashboardTypes';

const WORKSPACE_ENDPOINT = '/api/agno/workspaces';
const AGNO_AGENT_PREFIX = /^AGN_[A-Z0-9]+_v[0-9]+$/;

export class AgnoClient {
  async listWorkspaces(): Promise<AgnoWorkspaceSummary[]> {
    const response = await fetch(WORKSPACE_ENDPOINT);

    if (!response.ok) {
      throw new Error(`Unable to load Agno workspaces (${response.status})`);
    }

    const payload = (await response.json()) as AgnoWorkspaceSummary[];
    payload.forEach((workspace) => {
      workspace.agents.forEach((agent) => this.assertCanonicalName(agent));
    });

    return payload;
  }

  private assertCanonicalName(agent: AgentDefinition) {
    if (!AGNO_AGENT_PREFIX.test(agent.id)) {
      throw new Error(`Agno agent ${agent.id} violates canonical naming`);
    }
  }
}

export default new AgnoClient();
