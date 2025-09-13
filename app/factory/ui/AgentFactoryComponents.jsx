/**
 * Agent Factory UI Components for React Applications
 *
 * Production-ready React components for agent selection and swarm building
 * Can be integrated into existing React applications
 */

import React, { useState, useEffect, useCallback } from 'react';
import './AgentFactoryStyles.css'; // Import corresponding CSS file

// API Configuration
const API_BASE = '/api/factory';

// Utility Functions
export const showNotification = (message, type = 'info', duration = 3000) => {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <div class="flex items-center">
      <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} mr-2"></i>
      <span>${message}</span>
    </div>
  `;
  document.body.appendChild(notification);

  setTimeout(() => notification.classList.add('show'), 100);
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      if (document.body.contains(notification)) {
        document.body.removeChild(notification);
      }
    }, 300);
  }, duration);
};

// Agent Card Component
export const AgentCard = ({
  agent,
  selected = false,
  onSelect,
  onViewDetails,
  showSelectButton = true,
  className = ''
}) => {
  const getSpecialtyIcon = (specialty) => {
    const icons = {
      architect: 'fa-building',
      developer: 'fa-code',
      tester: 'fa-bug',
      devops: 'fa-server',
      security: 'fa-shield-alt',
      analyst: 'fa-chart-line',
      researcher: 'fa-search',
      product_manager: 'fa-tasks',
      data_scientist: 'fa-database',
      writer: 'fa-pen',
      designer: 'fa-paint-brush',
      marketer: 'fa-bullhorn',
      critic: 'fa-eye',
      orchestrator: 'fa-sitemap',
      planner: 'fa-calendar-alt',
      knowledge_worker: 'fa-brain'
    };
    return icons[specialty] || 'fa-user';
  };

  const handleCardClick = () => {
    if (showSelectButton && onSelect) {
      onSelect(agent);
    }
  };

  return (
    <div
      className={`agent-card ${selected ? 'selected' : ''} ${className}`}
      onClick={handleCardClick}
    >
      <div className="agent-card-header">
        <div className="agent-info">
          <div className="agent-avatar">
            <i className={`fas ${getSpecialtyIcon(agent.specialty)}`}></i>
          </div>
          <div className="agent-details">
            <h3 className="agent-name">{agent.metadata?.name || agent.name}</h3>
            <span className="specialty-badge">
              {agent.specialty?.replace('_', ' ')?.toUpperCase()}
            </span>
          </div>
        </div>
        <div className="agent-actions">
          <span className="agent-version">v{agent.metadata?.version || '1.0'}</span>
          {onViewDetails && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onViewDetails(agent);
              }}
              className="info-button"
              title="View Details"
            >
              <i className="fas fa-info-circle"></i>
            </button>
          )}
        </div>
      </div>

      <p className="agent-description">
        {agent.metadata?.description || agent.description || 'No description available'}
      </p>

      <div className="capabilities-section">
        <div className="capability-tags">
          {(agent.capabilities || []).slice(0, 3).map((cap, index) => (
            <span key={index} className="capability-tag">
              {cap.replace('_', ' ')}
            </span>
          ))}
          {(agent.capabilities || []).length > 3 && (
            <span className="capability-more">
              +{agent.capabilities.length - 3} more
            </span>
          )}
        </div>
      </div>

      <div className="agent-stats">
        <div className="stat-group">
          <div className="stat-item">
            <i className="fas fa-star"></i>
            <span>{((agent.metadata?.success_rate || 1) * 100).toFixed(1)}%</span>
          </div>
          <div className="stat-item">
            <i className="fas fa-clock"></i>
            <span>{agent.metadata?.usage_count || 0} uses</span>
          </div>
        </div>
        <span className="personality-label">
          {agent.personality?.replace('_', ' ') || 'analytical'}
        </span>
      </div>

      {showSelectButton && (
        <div className="agent-select-overlay">
          <div className="select-checkbox">
            <i className={`fas ${selected ? 'fa-check-circle' : 'fa-plus-circle'}`}></i>
          </div>
        </div>
      )}
    </div>
  );
};

// Swarm Template Card Component
export const SwarmTemplateCard = ({
  template,
  onSelect,
  onViewDetails,
  className = ''
}) => {
  const getTypeIcon = (type) => {
    const icons = {
      software_dev_team: 'fa-laptop-code',
      bi_analytics_team: 'fa-chart-bar',
      security_team: 'fa-shield-alt',
      coding: 'fa-code',
      debate: 'fa-comments',
      consensus: 'fa-handshake'
    };
    return icons[type] || 'fa-users';
  };

  return (
    <div className={`swarm-template-card ${className}`}>
      <div className="template-header">
        <div className="template-info">
          <div className="template-icon">
            <i className={`fas ${getTypeIcon(template.id || template.type)}`}></i>
          </div>
          <div className="template-details">
            <h3 className="template-name">{template.name}</h3>
            <span className="template-meta">
              {template.type} • {template.execution_mode}
            </span>
          </div>
        </div>
        {onViewDetails && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onViewDetails(template);
            }}
            className="info-button"
            title="View Details"
          >
            <i className="fas fa-info-circle"></i>
          </button>
        )}
      </div>

      <p className="template-description">{template.description}</p>

      <div className="template-requirements">
        <div className="requirements-label">Required Specialties:</div>
        <div className="specialty-tags">
          {(template.required_specialties || []).map((spec, index) => (
            <span key={index} className="specialty-tag">
              {spec.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>

      <div className="template-footer">
        <div className="template-stats">
          <span className="stat-item">
            <i className="fas fa-users"></i>
            Up to {template.max_agents || 5} agents
          </span>
          {template.agents_available !== undefined && (
            <span className="stat-item">
              <i className="fas fa-check-circle"></i>
              {template.agents_available} available
            </span>
          )}
        </div>
        <button
          onClick={() => onSelect && onSelect(template)}
          className="use-template-button"
          disabled={template.can_create === false}
        >
          Use Template
        </button>
      </div>
    </div>
  );
};

// Agent Filter Component
export const AgentFilters = ({
  searchTerm,
  onSearchChange,
  filterSpecialty,
  onSpecialtyChange,
  filterCapability,
  onCapabilityChange,
  specialties = [],
  capabilities = [],
  onClearFilters,
  className = ''
}) => {
  return (
    <div className={`agent-filters ${className}`}>
      <div className="filter-row">
        <div className="filter-group">
          <label className="filter-label">Search</label>
          <input
            type="text"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="filter-input"
          />
        </div>

        <div className="filter-group">
          <label className="filter-label">Specialty</label>
          <select
            value={filterSpecialty}
            onChange={(e) => onSpecialtyChange(e.target.value)}
            className="filter-select"
          >
            <option value="">All Specialties</option>
            {specialties.map(spec => (
              <option key={spec.id} value={spec.id}>{spec.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label className="filter-label">Capability</label>
          <select
            value={filterCapability}
            onChange={(e) => onCapabilityChange(e.target.value)}
            className="filter-select"
          >
            <option value="">All Capabilities</option>
            {capabilities.map(cap => (
              <option key={cap.id} value={cap.id}>{cap.name}</option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <button
            onClick={onClearFilters}
            className="clear-filters-button"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
};

// Selected Agents Panel Component
export const SelectedAgentsPanel = ({
  selectedAgents,
  onRemoveAgent,
  onClearAll,
  onCreateSwarm,
  loading = false,
  className = ''
}) => {
  if (selectedAgents.length === 0) {
    return null;
  }

  return (
    <div className={`selected-agents-panel ${className}`}>
      <div className="panel-header">
        <div className="panel-info">
          <h3 className="panel-title">
            Selected Agents ({selectedAgents.length})
          </h3>
          <p className="panel-subtitle">Create a custom swarm from your selection</p>
        </div>
        <div className="panel-actions">
          <button
            onClick={onClearAll}
            className="clear-button"
          >
            Clear Selection
          </button>
          <button
            onClick={onCreateSwarm}
            disabled={loading}
            className="create-button"
          >
            {loading && <div className="loading-spinner"></div>}
            Create Swarm
          </button>
        </div>
      </div>

      <div className="selected-agents-list">
        {selectedAgents.map(agent => (
          <span key={agent.id} className="selected-agent-tag">
            {agent.metadata?.name || agent.name}
            <button
              onClick={() => onRemoveAgent(agent)}
              className="remove-button"
            >
              <i className="fas fa-times"></i>
            </button>
          </span>
        ))}
      </div>
    </div>
  );
};

// Loading Component
export const LoadingSpinner = ({ message = 'Loading...', className = '' }) => {
  return (
    <div className={`loading-container ${className}`}>
      <div className="loading-spinner"></div>
      <span className="loading-message">{message}</span>
    </div>
  );
};

// Empty State Component
export const EmptyState = ({
  icon = 'fa-search',
  title = 'No results found',
  message = 'Try adjusting your criteria',
  className = ''
}) => {
  return (
    <div className={`empty-state ${className}`}>
      <i className={`fas ${icon} empty-state-icon`}></i>
      <h3 className="empty-state-title">{title}</h3>
      <p className="empty-state-message">{message}</p>
    </div>
  );
};

// Agent Grid Component
export const AgentGrid = ({
  agents,
  selectedAgents = [],
  onAgentSelect,
  onAgentViewDetails,
  loading = false,
  emptyMessage = 'No agents available',
  className = ''
}) => {
  if (loading) {
    return <LoadingSpinner message="Loading agents..." className={className} />;
  }

  if (agents.length === 0) {
    return (
      <EmptyState
        icon="fa-users"
        title="No agents found"
        message={emptyMessage}
        className={className}
      />
    );
  }

  return (
    <div className={`agent-grid ${className}`}>
      {agents.map(agent => (
        <AgentCard
          key={agent.id}
          agent={agent}
          selected={selectedAgents.some(a => a.id === agent.id)}
          onSelect={onAgentSelect}
          onViewDetails={onAgentViewDetails}
        />
      ))}
    </div>
  );
};

// Swarm Template Grid Component
export const SwarmTemplateGrid = ({
  templates,
  onTemplateSelect,
  onTemplateViewDetails,
  loading = false,
  emptyMessage = 'No templates available',
  className = ''
}) => {
  if (loading) {
    return <LoadingSpinner message="Loading templates..." className={className} />;
  }

  if (templates.length === 0) {
    return (
      <EmptyState
        icon="fa-layer-group"
        title="No templates found"
        message={emptyMessage}
        className={className}
      />
    );
  }

  return (
    <div className={`template-grid ${className}`}>
      {templates.map(template => (
        <SwarmTemplateCard
          key={template.id}
          template={template}
          onSelect={onTemplateSelect}
          onViewDetails={onTemplateViewDetails}
        />
      ))}
    </div>
  );
};

// Main Agent Factory Hook
export const useAgentFactory = () => {
  const [agents, setAgents] = useState([]);
  const [swarmTemplates, setSwarmTemplates] = useState([]);
  const [specialties, setSpecialties] = useState([]);
  const [capabilities, setCapabilities] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const apiCall = async (endpoint, options = {}) => {
    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`API call failed: ${endpoint}`, err);
      setError(err.message);
      throw err;
    }
  };

  const loadAgents = useCallback(async (filters = {}) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filters.specialty) params.append('specialty', filters.specialty);
      if (filters.capabilities) params.append('capabilities', filters.capabilities.join(','));
      if (filters.tags) params.append('tags', filters.tags.join(','));
      if (filters.search) params.append('search', filters.search);

      const data = await apiCall(`/inventory/agents?${params.toString()}`);
      setAgents(data.agents || []);
      return data;
    } catch (err) {
      setAgents([]);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSwarmTemplates = useCallback(async () => {
    try {
      const data = await apiCall('/inventory/swarm-templates');
      setSwarmTemplates(data.templates || []);
      return data;
    } catch (err) {
      setSwarmTemplates([]);
      throw err;
    }
  }, []);

  const loadSpecialties = useCallback(async () => {
    try {
      const data = await apiCall('/inventory/specialties');
      setSpecialties(data.specialties || []);
      return data;
    } catch (err) {
      setSpecialties([]);
      throw err;
    }
  }, []);

  const loadCapabilities = useCallback(async () => {
    try {
      const data = await apiCall('/inventory/capabilities');
      setCapabilities(data.capabilities || []);
      return data;
    } catch (err) {
      setCapabilities([]);
      throw err;
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const data = await apiCall('/inventory/stats');
      setStats(data);
      return data;
    } catch (err) {
      setStats({});
      throw err;
    }
  }, []);

  const createSwarmFromAgents = useCallback(async (selectedAgents, config = {}) => {
    const swarmConfig = {
      name: config.name || `Custom Swarm ${new Date().getTime()}`,
      description: config.description || 'Custom swarm created from selected agents',
      type: config.type || 'standard',
      execution_mode: config.execution_mode || 'parallel',
      required_specialties: [...new Set(selectedAgents.map(a => a.specialty))],
      max_agents: selectedAgents.length,
      ...config
    };

    return await apiCall('/inventory/swarms/create', {
      method: 'POST',
      body: JSON.stringify(swarmConfig)
    });
  }, []);

  const createSwarmFromTemplate = useCallback(async (templateId, overrides = {}) => {
    return await apiCall(`/inventory/swarms/from-template/${templateId}`, {
      method: 'POST',
      body: JSON.stringify(overrides)
    });
  }, []);

  const searchAgents = useCallback(async (query) => {
    setLoading(true);
    try {
      const data = await apiCall(`/inventory/agents?search=${encodeURIComponent(query)}`);
      setAgents(data.agents || []);
      return data;
    } catch (err) {
      setAgents([]);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const recommendAgents = useCallback(async (taskDescription, maxAgents = 5) => {
    return await apiCall('/inventory/recommend-agents', {
      method: 'POST',
      body: JSON.stringify({
        task_description: taskDescription,
        max_agents: maxAgents
      })
    });
  }, []);

  return {
    // State
    agents,
    swarmTemplates,
    specialties,
    capabilities,
    stats,
    loading,
    error,

    // Actions
    loadAgents,
    loadSwarmTemplates,
    loadSpecialties,
    loadCapabilities,
    loadStats,
    createSwarmFromAgents,
    createSwarmFromTemplate,
    searchAgents,
    recommendAgents,

    // Utilities
    apiCall
  };
};

// Complete Agent Factory Dashboard Component
export const AgentFactoryDashboard = ({
  className = '',
  defaultTab = 'inventory',
  onSwarmCreated,
  onAgentSelected,
  showTabs = true
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSpecialty, setFilterSpecialty] = useState('');
  const [filterCapability, setFilterCapability] = useState('');

  const {
    agents,
    swarmTemplates,
    specialties,
    capabilities,
    stats,
    loading,
    error,
    loadAgents,
    loadSwarmTemplates,
    loadSpecialties,
    loadCapabilities,
    loadStats,
    createSwarmFromAgents,
    createSwarmFromTemplate
  } = useAgentFactory();

  // Load initial data
  useEffect(() => {
    Promise.all([
      loadAgents(),
      loadSwarmTemplates(),
      loadSpecialties(),
      loadCapabilities(),
      loadStats()
    ]).catch(err => {
      console.error('Failed to load initial data:', err);
    });
  }, [loadAgents, loadSwarmTemplates, loadSpecialties, loadCapabilities, loadStats]);

  // Filter agents based on search and filters
  const filteredAgents = agents.filter(agent => {
    const matchesSearch = !searchTerm ||
      (agent.metadata?.name || agent.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (agent.metadata?.description || agent.description || '').toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSpecialty = !filterSpecialty || agent.specialty === filterSpecialty;

    const matchesCapability = !filterCapability ||
      (agent.capabilities || []).some(cap => cap === filterCapability);

    return matchesSearch && matchesSpecialty && matchesCapability;
  });

  const handleAgentSelect = (agent) => {
    const isSelected = selectedAgents.find(a => a.id === agent.id);
    let newSelection;

    if (isSelected) {
      newSelection = selectedAgents.filter(a => a.id !== agent.id);
    } else {
      newSelection = [...selectedAgents, agent];
    }

    setSelectedAgents(newSelection);
    onAgentSelected?.(agent, !isSelected);
  };

  const handleCreateSwarmFromSelection = async () => {
    if (selectedAgents.length === 0) {
      showNotification('Please select at least one agent', 'error');
      return;
    }

    try {
      const result = await createSwarmFromAgents(selectedAgents);
      showNotification(`Swarm created successfully: ${result.swarm_id}`, 'success');
      setSelectedAgents([]);
      onSwarmCreated?.(result);
    } catch (error) {
      showNotification('Failed to create swarm', 'error');
      console.error('Error creating swarm:', error);
    }
  };

  const handleTemplateSelect = async (template) => {
    try {
      const result = await createSwarmFromTemplate(template.id);
      showNotification(`Swarm created from template: ${result.swarm_id}`, 'success');
      onSwarmCreated?.(result);
    } catch (error) {
      showNotification('Failed to create swarm from template', 'error');
      console.error('Error creating swarm from template:', error);
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilterSpecialty('');
    setFilterCapability('');
  };

  const tabs = [
    { id: 'inventory', name: 'Agent Inventory', icon: 'fa-users' },
    { id: 'templates', name: 'Swarm Templates', icon: 'fa-layer-group' },
    { id: 'builder', name: 'Swarm Builder', icon: 'fa-cogs' }
  ];

  return (
    <div className={`agent-factory-dashboard ${className}`}>
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="header-info">
            <h1 className="dashboard-title">Agent Factory</h1>
            <p className="dashboard-subtitle">Centralized Agent & Swarm Management System</p>
          </div>
          <div className="header-stats">
            <div className="stat-item">
              <div className="stat-value">{stats.total_agents || 0}</div>
              <div className="stat-label">Agents</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{stats.total_swarms_created || 0}</div>
              <div className="stat-label">Swarms</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{((stats.average_success_rate || 0) * 100).toFixed(1)}%</div>
              <div className="stat-label">Success Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      {showTabs && (
        <div className="dashboard-tabs">
          <nav className="tab-nav">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              >
                <i className={`fas ${tab.icon}`}></i>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>
      )}

      {/* Content */}
      <div className="dashboard-content">
        {/* Error Display */}
        {error && (
          <div className="error-banner">
            <i className="fas fa-exclamation-triangle"></i>
            <span>Error: {error}</span>
            <button onClick={() => window.location.reload()} className="retry-button">
              Retry
            </button>
          </div>
        )}

        {/* Agent Inventory Tab */}
        {activeTab === 'inventory' && (
          <div className="tab-content">
            {/* Filters */}
            <AgentFilters
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              filterSpecialty={filterSpecialty}
              onSpecialtyChange={setFilterSpecialty}
              filterCapability={filterCapability}
              onCapabilityChange={setFilterCapability}
              specialties={specialties}
              capabilities={capabilities}
              onClearFilters={clearFilters}
              className="mb-6"
            />

            {/* Selected Agents Panel */}
            <SelectedAgentsPanel
              selectedAgents={selectedAgents}
              onRemoveAgent={handleAgentSelect}
              onClearAll={() => setSelectedAgents([])}
              onCreateSwarm={handleCreateSwarmFromSelection}
              loading={loading}
              className="mb-6"
            />

            {/* Agent Grid */}
            <AgentGrid
              agents={filteredAgents}
              selectedAgents={selectedAgents}
              onAgentSelect={handleAgentSelect}
              onAgentViewDetails={(agent) => showNotification(`Viewing details for ${agent.metadata?.name || agent.name}`, 'info')}
              loading={loading}
              emptyMessage="No agents match your search criteria"
            />
          </div>
        )}

        {/* Swarm Templates Tab */}
        {activeTab === 'templates' && (
          <div className="tab-content">
            <div className="section-header">
              <h2 className="section-title">Pre-built Swarm Templates</h2>
              <p className="section-subtitle">Choose from professionally designed swarm configurations for common use cases</p>
            </div>

            <SwarmTemplateGrid
              templates={swarmTemplates}
              onTemplateSelect={handleTemplateSelect}
              onTemplateViewDetails={(template) => showNotification(`Viewing details for ${template.name}`, 'info')}
              loading={loading}
              emptyMessage="No swarm templates are currently available"
            />
          </div>
        )}

        {/* Swarm Builder Tab */}
        {activeTab === 'builder' && (
          <div className="tab-content">
            <div className="section-header">
              <h2 className="section-title">Custom Swarm Builder</h2>
              <p className="section-subtitle">Build your own swarm configuration from scratch</p>
            </div>

            <EmptyState
              icon="fa-cogs"
              title="Custom Swarm Builder"
              message="Advanced swarm configuration interface coming soon. For now, use the Agent Inventory to select agents and create custom swarms."
              className="builder-placeholder"
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentFactoryDashboard;
