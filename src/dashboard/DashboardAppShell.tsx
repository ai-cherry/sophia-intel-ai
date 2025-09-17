import { useMemo, useState } from 'react';
import BusinessIntelligenceTab from './BusinessIntelligenceTab';
import AgentFactoryTab from './AgentFactoryTab';
import DeveloperStudioTab from './DeveloperStudioTab';
import type { DashboardTabConfig, TabKey } from '../lib/dashboardTypes';

const tabOrder: DashboardTabConfig[] = [
  {
    key: 'business-intelligence',
    label: 'Business Intelligence',
    description: 'Executive analytics and Pay Ready KPI monitoring.',
    component: BusinessIntelligenceTab
  },
  {
    key: 'agent-factory',
    label: 'Agent Factory',
    description: 'Flowwise workspace for employee-built automation agents.',
    component: AgentFactoryTab
  },
  {
    key: 'developer-studio',
    label: 'Developer Studio',
    description: 'Agno v2 orchestrations and advanced developer tooling.',
    component: DeveloperStudioTab
  }
];

const DashboardAppShell = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('business-intelligence');
  const activeConfig = useMemo(
    () => tabOrder.find((tab) => tab.key === activeTab) ?? tabOrder[0],
    [activeTab]
  );

  return (
    <div className="dashboard-shell">
      <header className="dashboard-header">
        <div>
          <h1>Pay Ready Intelligence Hub</h1>
          <p>{activeConfig.description}</p>
        </div>
        <nav className="dashboard-tabs" aria-label="Dashboard tabs">
          {tabOrder.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={tab.key === activeTab ? 'tab-active' : ''}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="dashboard-content">
        {activeTab === 'business-intelligence' && <BusinessIntelligenceTab />}
        {activeTab === 'agent-factory' && <AgentFactoryTab />}
        {activeTab === 'developer-studio' && <DeveloperStudioTab />}
      </main>
    </div>
  );
};

export default DashboardAppShell;
