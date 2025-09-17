export default function DashboardTab() {
  const handleKPIClick = (metric: string) => {
    alert(`Coming Soon: Detailed view for ${metric}`)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary mb-2">Business Overview</h2>
        <p className="text-secondary">Key performance indicators and business metrics</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <button
          onClick={() => handleKPIClick('Monthly Revenue')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center">
            <div className="text-2xl mr-3">💰</div>
            <div>
              <div className="text-2xl font-bold text-primary">$2.4M</div>
              <div className="text-sm text-secondary">Monthly Revenue</div>
            </div>
          </div>
        </button>

        <button
          onClick={() => handleKPIClick('Process Automation')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center">
            <div className="text-2xl mr-3">🎯</div>
            <div>
              <div className="text-2xl font-bold text-primary">87%</div>
              <div className="text-sm text-secondary">Process Automation</div>
            </div>
          </div>
        </button>

        <button
          onClick={() => handleKPIClick('Tasks Processed')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center">
            <div className="text-2xl mr-3">⚡</div>
            <div>
              <div className="text-2xl font-bold text-primary">156</div>
              <div className="text-sm text-secondary">Tasks Processed Today</div>
            </div>
          </div>
        </button>

        <button
          onClick={() => handleKPIClick('Efficiency Gain')}
          className="bg-card p-6 rounded-lg shadow hover:shadow-lg transition-all hover:scale-105 text-left border border-custom"
        >
          <div className="flex items-center">
            <div className="text-2xl mr-3">📈</div>
            <div>
              <div className="text-2xl font-bold text-primary">+23%</div>
              <div className="text-sm text-secondary">Efficiency Gain</div>
            </div>
          </div>
        </button>
      </div>

      {/* Recent Activities */}
      <div className="bg-card rounded-lg shadow border border-custom">
        <div className="px-6 py-4 border-b border-custom">
          <h3 className="text-lg font-medium text-primary">Recent Activities</h3>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <span className="text-green-500 mr-2">✅</span>
                <span className="text-primary">Sales pipeline analysis completed</span>
              </div>
              <span className="text-sm text-tertiary">2 minutes ago</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <span className="text-blue-500 mr-2">🔄</span>
                <span className="text-primary">Finance swarm processing invoices</span>
              </div>
              <span className="text-sm text-tertiary">5 minutes ago</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center">
                <span className="text-yellow-500 mr-2">⚠️</span>
                <span className="text-primary">Linear integration sync delayed</span>
              </div>
              <span className="text-sm text-tertiary">10 minutes ago</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}