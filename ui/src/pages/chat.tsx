import Link from 'next/link';
import { EndpointPicker } from '@/components/EndpointPicker';
import { TeamWorkflowPanel } from '@/components/TeamWorkflowPanel';
import { StreamView } from '@/components/StreamView';
import { useUIStore } from '@/state/ui';

export default function Chat() {
  const { isConnected } = useUIStore();
  const appName = process.env.NEXT_PUBLIC_APP_NAME || 'slim-agno';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="text-blue-600 hover:text-blue-700 transition-colors"
              >
                ← Back
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">
                {appName} - Team Chat
              </h1>
            </div>
            <div className="hidden md:block">
              <EndpointPicker />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!isConnected ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
            <p className="text-yellow-800 mb-4">
              Please connect to the Playground endpoint first.
            </p>
            <div className="max-w-md mx-auto">
              <EndpointPicker />
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left: Input Panel */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Configure & Run
              </h2>
              <TeamWorkflowPanel />
            </div>

            {/* Right: Output */}
            <div>
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Results
              </h2>
              <StreamView />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}