import Link from 'next/link';
import { EndpointPicker } from '@/components/EndpointPicker';

export default function Home() {
  const appName = process.env.NEXT_PUBLIC_APP_NAME || 'slim-agno';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">{appName}</h1>
            <div className="text-sm text-gray-500">
              Local-first AI Agent UI
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Endpoint Configuration */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Playground Connection
            </h2>
            <EndpointPicker />
          </section>

          {/* Quick Actions */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Quick Actions
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link
                href="/chat"
                className="block p-6 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
              >
                <h3 className="text-xl font-semibold text-blue-600 mb-2">
                  Open Chat
                </h3>
                <p className="text-gray-600">
                  Run teams with the Coding Swarm, Strategy Team, or custom agents.
                </p>
              </Link>

              <Link
                href="/workflow"
                className="block p-6 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
              >
                <h3 className="text-xl font-semibold text-blue-600 mb-2">
                  Open Workflow Runner
                </h3>
                <p className="text-gray-600">
                  Execute complex workflows like PR Lifecycle with quality gates.
                </p>
              </Link>

              <Link
                href="/swarm-configurator"
                className="block p-6 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow"
              >
                <h3 className="text-xl font-semibold text-blue-600 mb-2">
                  Swarm Configurator
                </h3>
                <p className="text-gray-600">
                  Tune parameters for swarm patterns including ConsensusSwarm.
                </p>
              </Link>
            </div>
          </section>

          {/* Features */}
          <section>
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Features
            </h2>
            <div className="bg-white rounded-lg shadow-sm p-6">
              <ul className="space-y-2">
                <li className="flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Local-first architecture (no secrets in browser)</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Real-time streaming responses</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Critic & Judge visualization</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Runner gate status (ALLOWED/BLOCKED)</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Tool call inspection</span>
                </li>
                <li className="flex items-center gap-2">
                  <span className="text-green-600">✓</span>
                  <span>Code citations with expandable previews</span>
                </li>
              </ul>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}