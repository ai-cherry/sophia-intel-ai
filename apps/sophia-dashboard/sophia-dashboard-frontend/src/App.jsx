import { useState } from 'react'
import Overview from './pages/Overview'
import Swarm from './pages/Swarm'
import Pipelines from './pages/Pipelines'
import Models from './pages/Models'
import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('overview')

  const pages = {
    overview: { component: Overview, title: 'Overview', icon: '📊' },
    swarm: { component: Swarm, title: 'Swarm', icon: '🤖' },
    pipelines: { component: Pipelines, title: 'Pipelines', icon: '🔄' },
    models: { component: Models, title: 'Models', icon: '⚡' }
  }

  const CurrentPageComponent = pages[currentPage].component

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <span className="text-white font-bold text-sm">S</span>
              </div>
              <div>
                <h1 className="text-white font-bold text-lg">Sophia Intel</h1>
                <p className="text-white/50 text-xs">MVP Dashboard</p>
              </div>
            </div>

            {/* Navigation Links */}
            <div className="flex items-center gap-1">
              {Object.entries(pages).map(([key, page]) => (
                <button
                  key={key}
                  onClick={() => setCurrentPage(key)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === key
                      ? 'bg-white/10 text-white'
                      : 'text-white/70 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <span>{page.icon}</span>
                  {page.title}
                </button>
              ))}
            </div>

            {/* Status Indicator */}
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-white/60 text-sm">Live</span>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <CurrentPageComponent />
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-sm mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="text-white/50 text-sm">
              © 2025 Sophia Intel • MVP Dashboard • Powered by MCP & LangGraph
            </div>
            <div className="flex items-center gap-4 text-white/40 text-sm">
              <span>Health: ✅</span>
              <span>Version: 1.0.0</span>
              <span>Build: {new Date().toISOString().slice(0, 10)}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App

