'use client'

import { useState } from 'react'
import { Tab } from '@headlessui/react'
import clsx from 'clsx'
import ThemeToggle from '../components/ui/ThemeToggle'
import { ThemeProvider } from '../hooks/useTheme'

// Tab components
import DashboardTab from '../components/tabs/DashboardTab'
import AgnoAgentsTab from '../components/tabs/AgnoAgentsTab'
import FlowiseTab from '../components/tabs/FlowiseTab'
import BusinessIntelligenceTab from '../components/tabs/BusinessIntelligenceTab'
import IntegrationsTab from '../components/tabs/IntegrationsTab'
import TrainingBrainTab from '../components/tabs/TrainingBrainTab'
import ProjectManagementTab from '../components/tabs/ProjectManagementTab'
import OperationsTab from '../components/tabs/OperationsTab'
import UnifiedSophiaChat from '../components/sophia/UnifiedSophiaChat'

const tabs = [
  { name: 'Dashboard', icon: '🏠', component: DashboardTab },
  { name: 'Agno Agents', icon: '🤖', component: AgnoAgentsTab },
  { name: 'Flowise', icon: '🌊', component: FlowiseTab },
  { name: 'Business Intelligence', icon: '📊', component: BusinessIntelligenceTab },
  { name: 'Integrations', icon: '🔗', component: IntegrationsTab },
  { name: 'Training Brain', icon: '🧠', component: TrainingBrainTab },
  { name: 'Project Management', icon: '📋', component: ProjectManagementTab },
  { name: 'Operations', icon: '⚙️', component: OperationsTab }
]

export default function SophiaIntelAIDashboard() {
  const [selectedTabIndex, setSelectedTabIndex] = useState(0)

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-primary">
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="mb-8 flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-primary">
                  Sophia Intelligence Hub
                </h1>
                <p className="text-secondary">
                  Business AI Command Center for Pay Ready
                </p>
              </div>
              <ThemeToggle />
            </div>

            <Tab.Group selectedIndex={selectedTabIndex} onChange={setSelectedTabIndex}>
              <Tab.List className="flex space-x-1 rounded-xl bg-accent/20 dark:bg-accent/10 p-1">
                {tabs.map((tab) => (
                  <Tab
                    key={tab.name}
                    className={({ selected }) =>
                      clsx(
                        'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
                        'ring-accent ring-opacity-60 ring-offset-2 ring-offset-accent focus:outline-none focus:ring-2',
                        selected
                          ? 'bg-card text-accent shadow'
                          : 'text-secondary hover:bg-card-hover hover:text-primary'
                      )
                    }
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.name}
                  </Tab>
                ))}
              </Tab.List>

              <Tab.Panels className="mt-6">
                {tabs.map((tab, idx) => (
                  <Tab.Panel
                    key={idx}
                    className="rounded-xl bg-card p-6 shadow-md border border-custom"
                  >
                    <tab.component />
                  </Tab.Panel>
                ))}
              </Tab.Panels>
            </Tab.Group>
          </div>
        </div>

        {/* Unified Sophia Chat with Full Backend Integration */}
        <UnifiedSophiaChat currentTab={tabs[selectedTabIndex]?.name || 'Dashboard'} />
      </div>
    </ThemeProvider>
  )
}