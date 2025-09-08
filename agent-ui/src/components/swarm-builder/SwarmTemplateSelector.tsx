/**
 * SwarmTemplateSelector - Template Gallery with Configuration Wizard
 * Provides UI for selecting, configuring, and deploying swarm templates
 * Features live code preview and Pay Ready business templates
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Grid,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tab,
  Tabs,
  TabPanel,
  IconButton,
  Alert,
  LinearProgress,
  Collapse,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Tooltip,
  Badge,
  Paper,
  Divider
} from '@mui/material';

import {
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayArrowIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  Timeline as TimelineIcon,
  Security as SecurityIcon,
  Business as BusinessIcon,
  Speed as SpeedIcon,
  Groups as GroupsIcon,
  Preview as PreviewIcon,
  Deploy as DeployIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';

import { useSwarmTemplates } from '../../hooks/useSwarmTemplates';

// ==============================================================================
// TYPE DEFINITIONS
// ==============================================================================

interface SwarmTemplate {
  id: string;
  name: string;
  description: string;
  topology: 'sequential' | 'star' | 'committee' | 'hierarchical';
  domain: 'sophia_business' | 'artemis_technical' | 'pay_ready' | 'cross_domain';
  category: string;
  agents: AgentTemplateConfig[];
  coordination_config: Record<string, any>;
  resource_limits: Record<string, any>;
  success_criteria: Record<string, any>;
  example_use_cases: string[];
  estimated_duration: string;
  complexity_level: number;
  pay_ready_optimized: boolean;
}

interface AgentTemplateConfig {
  template_name: string;
  role: string;
  factory_type: 'sophia' | 'artemis';
  custom_config: Record<string, any>;
  weight: number;
  required: boolean;
}

interface ConfigurationState {
  swarm_name: string;
  custom_config: Record<string, any>;
  agent_overrides: Record<string, any>;
  deployment_config: {
    auto_deploy: boolean;
    monitoring_enabled: boolean;
    notifications_enabled: boolean;
  };
}

// ==============================================================================
// COMPONENT IMPLEMENTATION
// ==============================================================================

const SwarmTemplateSelector: React.FC = () => {
  // Hooks
  const {
    templates,
    loading,
    error,
    generateCode,
    deploySwarm,
    getSwarmStatus,
    templateSummary
  } = useSwarmTemplates();

  // State
  const [selectedTemplate, setSelectedTemplate] = useState<SwarmTemplate | null>(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [configuration, setConfiguration] = useState<ConfigurationState>({
    swarm_name: '',
    custom_config: {},
    agent_overrides: {},
    deployment_config: {
      auto_deploy: false,
      monitoring_enabled: true,
      notifications_enabled: true
    }
  });
  const [activeTab, setActiveTab] = useState(0);
  const [generatedCode, setGeneratedCode] = useState<string>('');
  const [codePreviewOpen, setCodePreviewOpen] = useState(false);
  const [filters, setFilters] = useState({
    domain: '',
    topology: '',
    complexity: 5,
    pay_ready_only: false
  });
  const [deploymentStatus, setDeploymentStatus] = useState<'idle' | 'deploying' | 'deployed' | 'error'>('idle');

  // Filtered templates
  const filteredTemplates = useMemo(() => {
    if (!templates) return [];

    return templates.filter(template => {
      if (filters.domain && template.domain !== filters.domain) return false;
      if (filters.topology && template.topology !== filters.topology) return false;
      if (template.complexity_level > filters.complexity) return false;
      if (filters.pay_ready_only && !template.pay_ready_optimized) return false;
      return true;
    });
  }, [templates, filters]);

  // Reset configuration when template changes
  useEffect(() => {
    if (selectedTemplate) {
      setConfiguration({
        swarm_name: `${selectedTemplate.id}_${Date.now()}`,
        custom_config: {},
        agent_overrides: {},
        deployment_config: {
          auto_deploy: false,
          monitoring_enabled: true,
          notifications_enabled: true
        }
      });
    }
  }, [selectedTemplate]);

  // ==============================================================================
  // EVENT HANDLERS
  // ==============================================================================

  const handleTemplateSelect = (template: SwarmTemplate) => {
    setSelectedTemplate(template);
    setConfigDialogOpen(true);
  };

  const handleConfigurationChange = (key: string, value: any) => {
    setConfiguration(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleAgentOverride = (agentIndex: number, configKey: string, value: any) => {
    setConfiguration(prev => ({
      ...prev,
      agent_overrides: {
        ...prev.agent_overrides,
        [agentIndex]: {
          ...prev.agent_overrides[agentIndex],
          [configKey]: value
        }
      }
    }));
  };

  const handleGenerateCode = async () => {
    if (!selectedTemplate) return;

    try {
      const result = await generateCode(selectedTemplate.id, configuration.custom_config, configuration.swarm_name);
      if (result.success) {
        setGeneratedCode(result.code);
        setCodePreviewOpen(true);
      }
    } catch (error) {
      console.error('Failed to generate code:', error);
    }
  };

  const handleDeploy = async () => {
    if (!selectedTemplate) return;

    try {
      setDeploymentStatus('deploying');

      const result = await deploySwarm({
        template_id: selectedTemplate.id,
        swarm_name: configuration.swarm_name,
        custom_config: configuration.custom_config,
        agent_overrides: configuration.agent_overrides,
        auto_deploy: configuration.deployment_config.auto_deploy
      });

      if (result.success) {
        setDeploymentStatus('deployed');
        setConfigDialogOpen(false);
      } else {
        setDeploymentStatus('error');
      }
    } catch (error) {
      console.error('Deployment failed:', error);
      setDeploymentStatus('error');
    }
  };

  // ==============================================================================
  // RENDER HELPERS
  // ==============================================================================

  const getTopologyIcon = (topology: string) => {
    switch (topology) {
      case 'sequential': return <TimelineIcon />;
      case 'star': return <GroupsIcon />;
      case 'committee': return <SecurityIcon />;
      case 'hierarchical': return <BusinessIcon />;
      default: return <CodeIcon />;
    }
  };

  const getDomainColor = (domain: string) => {
    switch (domain) {
      case 'sophia_business': return 'primary';
      case 'artemis_technical': return 'secondary';
      case 'pay_ready': return 'success';
      case 'cross_domain': return 'warning';
      default: return 'default';
    }
  };

  const getComplexityColor = (level: number) => {
    if (level <= 2) return 'success';
    if (level <= 3) return 'warning';
    return 'error';
  };

  // ==============================================================================
  // MAIN RENDER
  // ==============================================================================

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Swarm Template Gallery
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Select and configure pre-built swarm templates for your business intelligence and technical operations
        </Typography>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Domain</InputLabel>
              <Select
                value={filters.domain}
                label="Domain"
                onChange={(e) => setFilters(prev => ({ ...prev, domain: e.target.value }))}
              >
                <MenuItem value="">All Domains</MenuItem>
                <MenuItem value="sophia_business">Sophia Business</MenuItem>
                <MenuItem value="artemis_technical">Artemis Technical</MenuItem>
                <MenuItem value="pay_ready">Pay Ready</MenuItem>
                <MenuItem value="cross_domain">Cross Domain</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Topology</InputLabel>
              <Select
                value={filters.topology}
                label="Topology"
                onChange={(e) => setFilters(prev => ({ ...prev, topology: e.target.value }))}
              >
                <MenuItem value="">All Topologies</MenuItem>
                <MenuItem value="sequential">Sequential</MenuItem>
                <MenuItem value="star">Star</MenuItem>
                <MenuItem value="committee">Committee</MenuItem>
                <MenuItem value="hierarchical">Hierarchical</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6} md={2}>
            <TextField
              fullWidth
              size="small"
              type="number"
              label="Max Complexity"
              value={filters.complexity}
              onChange={(e) => setFilters(prev => ({ ...prev, complexity: parseInt(e.target.value) || 5 }))}
              inputProps={{ min: 1, max: 5 }}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={filters.pay_ready_only}
                  onChange={(e) => setFilters(prev => ({ ...prev, pay_ready_only: e.target.checked }))}
                />
              }
              label="Pay Ready Only"
            />
          </Grid>

          <Grid item xs={12} md={3}>
            <Typography variant="body2" color="text.secondary">
              {filteredTemplates.length} templates available
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Loading State */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Template Grid */}
      <Grid container spacing={3}>
        {filteredTemplates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                {/* Template Header */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    {getTopologyIcon(template.topology)}
                    <Typography variant="h6" sx={{ ml: 1, flexGrow: 1 }}>
                      {template.name}
                    </Typography>
                    {template.pay_ready_optimized && (
                      <Badge badgeContent="Pay Ready" color="success" />
                    )}
                  </Box>

                  <Typography variant="body2" color="text.secondary">
                    {template.description}
                  </Typography>
                </Box>

                {/* Template Chips */}
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                  <Chip
                    label={template.domain.replace('_', ' ')}
                    size="small"
                    color={getDomainColor(template.domain)}
                  />
                  <Chip
                    label={`${template.topology} topology`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    label={`Level ${template.complexity_level}`}
                    size="small"
                    color={getComplexityColor(template.complexity_level)}
                  />
                </Box>

                {/* Template Stats */}
                <Grid container spacing={1} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Agents: {template.agents.length}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Duration: {template.estimated_duration}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Max Tasks: {template.resource_limits.max_concurrent_tasks}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Category: {template.category.replace('_', ' ')}
                    </Typography>
                  </Grid>
                </Grid>

                {/* Use Cases */}
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 'bold' }}>
                  Use Cases:
                </Typography>
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                  {template.example_use_cases.slice(0, 2).join(', ')}
                  {template.example_use_cases.length > 2 && '...'}
                </Typography>
              </CardContent>

              <CardActions>
                <Button
                  variant="contained"
                  startIcon={<SettingsIcon />}
                  onClick={() => handleTemplateSelect(template)}
                  fullWidth
                >
                  Configure & Deploy
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Configuration Dialog */}
      <Dialog
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            Configure Swarm: {selectedTemplate?.name}
            <IconButton onClick={() => setConfigDialogOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent>
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab label="Basic Configuration" />
            <Tab label="Agent Customization" />
            <Tab label="Advanced Settings" />
            <Tab label="Preview" />
          </Tabs>

          {/* Tab 0: Basic Configuration */}
          {activeTab === 0 && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Swarm Name"
                    value={configuration.swarm_name}
                    onChange={(e) => handleConfigurationChange('swarm_name', e.target.value)}
                    helperText="Unique identifier for your swarm instance"
                  />
                </Grid>

                {selectedTemplate && (
                  <>
                    <Grid item xs={12}>
                      <Typography variant="h6" gutterBottom>
                        Template Information
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2">
                            <strong>Topology:</strong> {selectedTemplate.topology}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2">
                            <strong>Domain:</strong> {selectedTemplate.domain.replace('_', ' ')}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2">
                            <strong>Agents:</strong> {selectedTemplate.agents.length}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2">
                            <strong>Estimated Duration:</strong> {selectedTemplate.estimated_duration}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Grid>

                    <Grid item xs={12}>
                      <Typography variant="h6" gutterBottom>
                        Resource Requirements
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2">
                            <strong>Max Concurrent Tasks:</strong> {selectedTemplate.resource_limits.max_concurrent_tasks}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2">
                            <strong>Memory (MB):</strong> {selectedTemplate.resource_limits.memory_usage_mb}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                          <Typography variant="body2">
                            <strong>API Calls/Min:</strong> {selectedTemplate.resource_limits.api_calls_per_minute}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Grid>
                  </>
                )}
              </Grid>
            </Box>
          )}

          {/* Tab 1: Agent Customization */}
          {activeTab === 1 && selectedTemplate && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Agent Configuration
              </Typography>
              {selectedTemplate.agents.map((agent, index) => (
                <Accordion key={index}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Chip
                        label={agent.factory_type}
                        size="small"
                        color={agent.factory_type === 'sophia' ? 'primary' : 'secondary'}
                      />
                      <Typography>{agent.template_name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        ({agent.role})
                      </Typography>
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <TextField
                          fullWidth
                          size="small"
                          label="Weight"
                          type="number"
                          value={configuration.agent_overrides[index]?.weight || agent.weight}
                          onChange={(e) => handleAgentOverride(index, 'weight', parseFloat(e.target.value))}
                        />
                      </Grid>
                      <Grid item xs={12} sm={6}>
                        <FormControlLabel
                          control={
                            <Switch
                              checked={configuration.agent_overrides[index]?.required !== false ? agent.required : false}
                              onChange={(e) => handleAgentOverride(index, 'required', e.target.checked)}
                            />
                          }
                          label="Required"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Custom Configuration (JSON)
                        </Typography>
                        <TextField
                          fullWidth
                          multiline
                          rows={3}
                          size="small"
                          placeholder='{"temperature": 0.3, "custom_param": "value"}'
                          value={JSON.stringify(configuration.agent_overrides[index]?.custom_config || {}, null, 2)}
                          onChange={(e) => {
                            try {
                              const config = JSON.parse(e.target.value || '{}');
                              handleAgentOverride(index, 'custom_config', config);
                            } catch {
                              // Invalid JSON - ignore
                            }
                          }}
                        />
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ))}
            </Box>
          )}

          {/* Tab 2: Advanced Settings */}
          {activeTab === 2 && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Deployment Configuration
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={configuration.deployment_config.auto_deploy}
                        onChange={(e) => handleConfigurationChange('deployment_config', {
                          ...configuration.deployment_config,
                          auto_deploy: e.target.checked
                        })}
                      />
                    }
                    label="Auto Deploy After Generation"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={configuration.deployment_config.monitoring_enabled}
                        onChange={(e) => handleConfigurationChange('deployment_config', {
                          ...configuration.deployment_config,
                          monitoring_enabled: e.target.checked
                        })}
                      />
                    }
                    label="Enable Monitoring"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={configuration.deployment_config.notifications_enabled}
                        onChange={(e) => handleConfigurationChange('deployment_config', {
                          ...configuration.deployment_config,
                          notifications_enabled: e.target.checked
                        })}
                      />
                    }
                    label="Enable Notifications"
                  />
                </Grid>
              </Grid>

              <Divider sx={{ my: 3 }} />

              <Typography variant="h6" gutterBottom>
                Global Custom Configuration
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={6}
                label="Custom Configuration (JSON)"
                placeholder='{"global_timeout": 30, "retry_attempts": 3}'
                value={JSON.stringify(configuration.custom_config, null, 2)}
                onChange={(e) => {
                  try {
                    const config = JSON.parse(e.target.value || '{}');
                    handleConfigurationChange('custom_config', config);
                  } catch {
                    // Invalid JSON - ignore
                  }
                }}
              />
            </Box>
          )}

          {/* Tab 3: Preview */}
          {activeTab === 3 && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Configuration Preview
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <pre style={{ fontSize: '12px', overflow: 'auto', maxHeight: '400px' }}>
                  {JSON.stringify({
                    template_id: selectedTemplate?.id,
                    swarm_name: configuration.swarm_name,
                    custom_config: configuration.custom_config,
                    agent_overrides: configuration.agent_overrides,
                    deployment_config: configuration.deployment_config
                  }, null, 2)}
                </pre>
              </Paper>
            </Box>
          )}
        </DialogContent>

        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>
            Cancel
          </Button>
          <Button
            startIcon={<PreviewIcon />}
            onClick={handleGenerateCode}
            disabled={!configuration.swarm_name}
          >
            Generate Code
          </Button>
          <Button
            variant="contained"
            startIcon={<DeployIcon />}
            onClick={handleDeploy}
            disabled={!configuration.swarm_name || deploymentStatus === 'deploying'}
          >
            {deploymentStatus === 'deploying' ? 'Deploying...' : 'Deploy Swarm'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Code Preview Dialog */}
      <Dialog
        open={codePreviewOpen}
        onClose={() => setCodePreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Generated Swarm Code
          <IconButton
            sx={{ position: 'absolute', right: 8, top: 8 }}
            onClick={() => setCodePreviewOpen(false)}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Paper sx={{ p: 2, bgcolor: 'grey.900', color: 'common.white', maxHeight: '600px', overflow: 'auto' }}>
            <pre style={{ fontSize: '12px', fontFamily: 'monospace', margin: 0 }}>
              {generatedCode}
            </pre>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCodePreviewOpen(false)}>
            Close
          </Button>
          <Button
            variant="contained"
            onClick={() => {
              navigator.clipboard.writeText(generatedCode);
            }}
          >
            Copy Code
          </Button>
        </DialogActions>
      </Dialog>

      {/* Summary Stats */}
      {templateSummary && (
        <Paper sx={{ p: 2, mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            Template Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">
                <strong>Total Templates:</strong> {templateSummary.total_templates}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">
                <strong>Pay Ready:</strong> {templateSummary.pay_ready_count}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">
                <strong>Sophia Business:</strong> {templateSummary.by_domain?.sophia_business || 0}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="body2">
                <strong>Artemis Technical:</strong> {templateSummary.by_domain?.artemis_technical || 0}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default SwarmTemplateSelector;
