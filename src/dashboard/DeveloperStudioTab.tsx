import { useEffect, useState } from 'react';
import agnoClient from '../agents/agno-v2/AgnoClient';
import type { AgnoWorkspaceSummary } from '../lib/dashboardTypes';

const DeveloperStudioTab = () => {
  const [workspaces, setWorkspaces] = useState<AgnoWorkspaceSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadWorkspaces = async () => {
      try {
        const payload = await agnoClient.listWorkspaces();
        if (!cancelled) {
          setWorkspaces(payload);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError((err as Error).message);
        }
      }
    };

    loadWorkspaces();
    const interval = window.setInterval(loadWorkspaces, 120_000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  if (error) {
    return (
      <section className="panel error">
        <h2>Agno v2 Connectivity Issue</h2>
        <p>{error}</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <h2>Developer Studio</h2>
        <p>Admin-only orchestrations powered by Agno v2 pipelines.</p>
      </header>

      <div className="workspace-grid">
        {workspaces.map((workspace) => (
          <article key={workspace.id} className={`workspace-card health-${workspace.health}`}>
            <header className="workspace-header">
              <div>
                <h3>{workspace.purpose}</h3>
                <span>{workspace.maintainer}</span>
              </div>
              <span className="workspace-health">{workspace.health}</span>
            </header>

            <dl className="workspace-meta">
              <div>
                <dt>Pipelines</dt>
                <dd>{workspace.pipelines}</dd>
              </div>
              <div>
                <dt>Version</dt>
                <dd>{workspace.version}</dd>
              </div>
            </dl>

            <div className="workspace-agents">
              <h4>Agno Agents</h4>
              <ul>
                {workspace.agents.map((agent) => (
                  <li key={agent.id}>
                    <span className="agent-name">{agent.name}</span>
                    <span className="agent-version">{agent.version}</span>
                    <span className="agent-tags">{agent.tags?.join(', ')}</span>
                  </li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
};

export default DeveloperStudioTab;
