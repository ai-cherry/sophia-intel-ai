/**
 * Prompt Library Dashboard
 * Comprehensive UI for prompt management with Monaco editor and version visualization
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  TextField,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  CardHeader,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  LinearProgress,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  History as HistoryIcon,
  CompareArrows as CompareIcon,
  BranchingScheme as BranchIcon,
  MergeType as MergeIcon,
  Science as ABTestIcon,
  Analytics as AnalyticsIcon,
  Download as ExportIcon,
  Upload as ImportIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Visibility as ViewIcon,
  Code as CodeIcon,
  AutoAwesome as AIIcon,
  Timeline as TimelineIcon,
  Assessment as MetricsIcon,
} from '@mui/icons-material';
import { Editor } from '@monaco-editor/react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { styled } from '@mui/material/styles';

import { usePromptLibrary } from '../../hooks/usePromptLibrary';

// Styled components
const DashboardContainer = styled(Box)(({ theme }) => ({
  height: '100vh',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: theme.palette.background.default,
}));

const HeaderBar = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(2),
  marginBottom: theme.spacing(2),
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
  color: theme.palette.primary.contrastText,
}));

const ContentArea = styled(Box)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  gap: theme.spacing(2),
  padding: theme.spacing(0, 2, 2, 2),
  overflow: 'hidden',
}));

const SidePanel = styled(Paper)(({ theme }) => ({
  width: '300px',
  padding: theme.spacing(2),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(2),
  maxHeight: '100%',
  overflow: 'auto',
}));

const MainEditor = styled(Paper)(({ theme }) => ({
  flex: 1,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}));

const EditorTabs = styled(Tabs)(({ theme }) => ({
  borderBottom: `1px solid ${theme.palette.divider}`,
  minHeight: 48,
}));

const EditorContainer = styled(Box)(() => ({
  flex: 1,
  position: 'relative',
  '& .monaco-editor': {
    borderRadius: 0,
  },
}));

const MetricsPanel = styled(Paper)(({ theme }) => ({
  width: '350px',
  padding: theme.spacing(2),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(2),
  maxHeight: '100%',
  overflow: 'auto',
}));

// Types
interface PromptVersion {
  id: string;
  prompt_id: string;
  branch: string;
  version: string;
  content: string;
  metadata: {
    domain: string;
    agent_name: string;
    task_type: string;
    business_context: string[];
    performance_tags: string[];
    author: string;
  };
  status: string;
  created_at: string;
  performance_metrics?: { [key: string]: number };
}

interface Branch {
  name: string;
  base_version: string;
  head_version: string;
  created_at: string;
  description?: string;
  is_merged: boolean;
}

interface ABTest {
  test_id: string;
  name: string;
  description: string;
  control_version: string;
  test_versions: string[];
  traffic_split: { [key: string]: number };
  success_metrics: string[];
  start_time: string;
  end_time?: string;
  status: string;
}

// Main Dashboard Component
export const PromptLibraryDashboard: React.FC = () => {
  const {
    prompts,
    branches,
    abTests,
    searchPrompts,
    createPrompt,
    updatePrompt,
    deletePrompt,
    createBranch,
    mergeBranch,
    diffVersions,
    createABTest,
    recordABTestResult,
    getABTestResults,
    updateMetrics,
    getLeaderboard,
    exportPrompts,
    importPrompts,
    loading,
    error
  } = usePromptLibrary();

  // State management
  const [selectedPrompt, setSelectedPrompt] = useState<PromptVersion | null>(null);
  const [selectedBranch, setSelectedBranch] = useState<string>('main');
  const [currentTab, setCurrentTab] = useState(0);
  const [editorContent, setEditorContent] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDomain, setFilterDomain] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showBranchDialog, setShowBranchDialog] = useState(false);
  const [showMergeDialog, setShowMergeDialog] = useState(false);
  const [showABTestDialog, setShowABTestDialog] = useState(false);
  const [showVersionHistory, setShowVersionHistory] = useState(false);
  const [showDiffView, setShowDiffView] = useState(false);
  const [diffVersions, setDiffVersions] = useState<{from: string, to: string} | null>(null);
  const [leaderboardData, setLeaderboardData] = useState<any[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<any[]>([]);

  // Filtered prompts based on search and filters
  const filteredPrompts = useMemo(() => {
    return prompts.filter(prompt => {
      const matchesSearch = !searchQuery ||
        prompt.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
        prompt.metadata.agent_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        prompt.prompt_id.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesDomain = !filterDomain || prompt.metadata.domain === filterDomain;
      const matchesAgent = !filterAgent || prompt.metadata.agent_name === filterAgent;

      return matchesSearch && matchesDomain && matchesAgent;
    });
  }, [prompts, searchQuery, filterDomain, filterAgent]);

  // Load leaderboard data
  useEffect(() => {
    const loadLeaderboard = async () => {
      try {
        const data = await getLeaderboard(filterDomain, 'success_rate', 10);
        setLeaderboardData(data);
      } catch (error) {
        console.error('Failed to load leaderboard:', error);
      }
    };
    loadLeaderboard();
  }, [filterDomain, getLeaderboard]);

  // Handle prompt selection
  const handlePromptSelect = useCallback((prompt: PromptVersion) => {
    setSelectedPrompt(prompt);
    setEditorContent(prompt.content);
    setSelectedBranch(prompt.branch);
  }, []);

  // Handle editor content change
  const handleEditorChange = useCallback((value: string | undefined) => {
    setEditorContent(value || '');
  }, []);

  // Save prompt changes
  const handleSavePrompt = useCallback(async () => {
    if (!selectedPrompt) return;

    try {
      await updatePrompt(selectedPrompt.prompt_id, {
        content: editorContent,
        branch: selectedBranch,
        commit_message: `Update ${selectedPrompt.metadata.task_type} prompt`
      });
    } catch (error) {
      console.error('Failed to save prompt:', error);
    }
  }, [selectedPrompt, editorContent, selectedBranch, updatePrompt]);

  // Create new prompt
  const handleCreatePrompt = useCallback(async (promptData: any) => {
    try {
      await createPrompt(promptData);
      setShowCreateDialog(false);
    } catch (error) {
      console.error('Failed to create prompt:', error);
    }
  }, [createPrompt]);

  // Create branch
  const handleCreateBranch = useCallback(async (branchData: any) => {
    if (!selectedPrompt) return;

    try {
      await createBranch(selectedPrompt.prompt_id, branchData);
      setShowBranchDialog(false);
    } catch (error) {
      console.error('Failed to create branch:', error);
    }
  }, [selectedPrompt, createBranch]);

  // Render tab panels
  const renderTabPanel = (value: number, index: number, children: React.ReactNode) => (
    <div hidden={value !== index} style={{ flex: 1, display: value === index ? 'flex' : 'none', flexDirection: 'column' }}>
      {children}
    </div>
  );

  // Render prompt list
  const renderPromptList = () => (
    <List>
      {filteredPrompts.map((prompt) => (
        <ListItem
          key={prompt.id}
          button
          selected={selectedPrompt?.id === prompt.id}
          onClick={() => handlePromptSelect(prompt)}
          secondaryAction={
            <Box>
              <Tooltip title="View History">
                <IconButton size="small" onClick={() => setShowVersionHistory(true)}>
                  <HistoryIcon />
                </IconButton>
              </Tooltip>
              <Tooltip title="Compare Versions">
                <IconButton size="small" onClick={() => setShowDiffView(true)}>
                  <CompareIcon />
                </IconButton>
              </Tooltip>
            </Box>
          }
        >
          <ListItemIcon>
            <CodeIcon color={prompt.status === 'active' ? 'primary' : 'disabled'} />
          </ListItemIcon>
          <ListItemText
            primary={
              <Box display="flex" alignItems="center" gap={1}>
                <Typography variant="subtitle2" noWrap>
                  {prompt.metadata.agent_name || 'Unknown'} - {prompt.metadata.task_type}
                </Typography>
                <Chip size="small" label={prompt.branch} color="secondary" />
                <Chip size="small" label={prompt.version} variant="outlined" />
              </Box>
            }
            secondary={
              <Box>
                <Typography variant="caption" color="textSecondary" noWrap>
                  {prompt.prompt_id}
                </Typography>
                <Box display="flex" gap={0.5} flexWrap="wrap" mt={0.5}>
                  <Chip size="small" label={prompt.metadata.domain} color="primary" variant="outlined" />
                  {prompt.metadata.performance_tags?.map((tag) => (
                    <Chip key={tag} size="small" label={tag} variant="outlined" />
                  ))}
                </Box>
              </Box>
            }
          />
        </ListItem>
      ))}
    </List>
  );

  // Render performance metrics
  const renderPerformanceMetrics = () => (
    <Card>
      <CardHeader
        title="Performance Analytics"
        action={
          <IconButton onClick={() => window.location.reload()}>
            <RefreshIcon />
          </IconButton>
        }
      />
      <CardContent>
        {leaderboardData.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={leaderboardData.slice(0, 5)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="agent_name"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis />
              <ChartTooltip />
              <Bar dataKey="score" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <Typography variant="body2" color="textSecondary">
            No performance data available
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  // Render A/B test status
  const renderABTestStatus = () => (
    <Card>
      <CardHeader
        title="A/B Tests"
        action={
          <Button
            startIcon={<ABTestIcon />}
            variant="outlined"
            size="small"
            onClick={() => setShowABTestDialog(true)}
          >
            New Test
          </Button>
        }
      />
      <CardContent>
        {abTests.length > 0 ? (
          <List dense>
            {abTests.slice(0, 3).map((test) => (
              <ListItem key={test.test_id}>
                <ListItemText
                  primary={test.name}
                  secondary={`Status: ${test.status} • Started: ${new Date(test.start_time).toLocaleDateString()}`}
                />
                <Chip
                  size="small"
                  label={test.status}
                  color={test.status === 'active' ? 'success' : 'default'}
                />
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="textSecondary">
            No active A/B tests
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  // Render branch visualization
  const renderBranchVisualization = () => (
    <Card>
      <CardHeader
        title="Branch Overview"
        action={
          <Button
            startIcon={<BranchIcon />}
            variant="outlined"
            size="small"
            onClick={() => setShowBranchDialog(true)}
          >
            New Branch
          </Button>
        }
      />
      <CardContent>
        {selectedPrompt && branches[selectedPrompt.prompt_id] ? (
          <List dense>
            {branches[selectedPrompt.prompt_id].map((branch) => (
              <ListItem key={branch.name}>
                <ListItemIcon>
                  <BranchIcon color={branch.is_merged ? 'disabled' : 'primary'} />
                </ListItemIcon>
                <ListItemText
                  primary={branch.name}
                  secondary={branch.description || `Created: ${new Date(branch.created_at).toLocaleDateString()}`}
                />
                {!branch.is_merged && branch.name !== 'main' && (
                  <Button
                    size="small"
                    startIcon={<MergeIcon />}
                    onClick={() => setShowMergeDialog(true)}
                  >
                    Merge
                  </Button>
                )}
              </ListItem>
            ))}
          </List>
        ) : (
          <Typography variant="body2" color="textSecondary">
            Select a prompt to view branches
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  return (
    <DashboardContainer>
      {/* Header */}
      <HeaderBar elevation={2}>
        <Box display="flex" alignItems="center" gap={2}>
          <AIIcon fontSize="large" />
          <Box>
            <Typography variant="h5" fontWeight="bold">
              Prompt Library Dashboard
            </Typography>
            <Typography variant="subtitle2" opacity={0.8}>
              Git-like versioning for mythology agent prompts
            </Typography>
          </Box>
        </Box>

        <Box display="flex" gap={1}>
          <Button
            startIcon={<AddIcon />}
            variant="contained"
            color="secondary"
            onClick={() => setShowCreateDialog(true)}
          >
            New Prompt
          </Button>
          <Button
            startIcon={<ExportIcon />}
            variant="outlined"
            color="inherit"
            onClick={() => exportPrompts()}
          >
            Export
          </Button>
          <Button
            startIcon={<ImportIcon />}
            variant="outlined"
            color="inherit"
            onClick={() => {/* Handle import */}}
          >
            Import
          </Button>
        </Box>
      </HeaderBar>

      {/* Main Content */}
      <ContentArea>
        {/* Left Sidebar - Search & Browse */}
        <SidePanel elevation={1}>
          <Typography variant="h6" gutterBottom>
            Browse Prompts
          </Typography>

          {/* Search */}
          <TextField
            placeholder="Search prompts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            fullWidth
            size="small"
            InputProps={{
              startAdornment: <SearchIcon color="action" />,
            }}
          />

          {/* Filters */}
          <Box display="flex" gap={1}>
            <FormControl size="small" fullWidth>
              <InputLabel>Domain</InputLabel>
              <Select
                value={filterDomain}
                label="Domain"
                onChange={(e) => setFilterDomain(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="sophia">Sophia</MenuItem>
                <MenuItem value="sophia">Sophia</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" fullWidth>
              <InputLabel>Agent</InputLabel>
              <Select
                value={filterAgent}
                label="Agent"
                onChange={(e) => setFilterAgent(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="hermes">Hermes</MenuItem>
                <MenuItem value="athena">Athena</MenuItem>
                <MenuItem value="asclepius">Asclepius</MenuItem>
                <MenuItem value="odin">Odin</MenuItem>
                <MenuItem value="minerva">Minerva</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Divider />

          {/* Prompt List */}
          <Box flex={1} overflow="auto">
            {loading ? (
              <LinearProgress />
            ) : (
              renderPromptList()
            )}
          </Box>
        </SidePanel>

        {/* Main Editor Area */}
        <MainEditor elevation={1}>
          <EditorTabs
            value={currentTab}
            onChange={(_, newValue) => setCurrentTab(newValue)}
          >
            <Tab
              icon={<EditIcon />}
              label="Editor"
              iconPosition="start"
            />
            <Tab
              icon={<HistoryIcon />}
              label="History"
              iconPosition="start"
            />
            <Tab
              icon={<CompareIcon />}
              label="Compare"
              iconPosition="start"
            />
            <Tab
              icon={<AnalyticsIcon />}
              label="Analytics"
              iconPosition="start"
            />
          </EditorTabs>

          {/* Tab Panels */}
          {renderTabPanel(0, 0,
            <Box display="flex" flexDirection="column" height="100%">
              {/* Editor Toolbar */}
              <Box display="flex" justifyContent="between" alignItems="center" p={1} bgcolor="grey.50">
                <Box display="flex" alignItems="center" gap={1}>
                  <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Branch</InputLabel>
                    <Select
                      value={selectedBranch}
                      label="Branch"
                      onChange={(e) => setSelectedBranch(e.target.value)}
                    >
                      <MenuItem value="main">main</MenuItem>
                      {selectedPrompt && branches[selectedPrompt.prompt_id]?.map((branch) => (
                        <MenuItem key={branch.name} value={branch.name}>
                          {branch.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {selectedPrompt && (
                    <Typography variant="body2" color="textSecondary">
                      {selectedPrompt.metadata.agent_name} • {selectedPrompt.metadata.task_type}
                    </Typography>
                  )}
                </Box>

                <Box display="flex" gap={1}>
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleSavePrompt}
                    disabled={!selectedPrompt || !editorContent.trim()}
                  >
                    Save Changes
                  </Button>
                </Box>
              </Box>

              {/* Monaco Editor */}
              <EditorContainer>
                <Editor
                  height="100%"
                  defaultLanguage="markdown"
                  theme="vs-dark"
                  value={editorContent}
                  onChange={handleEditorChange}
                  options={{
                    minimap: { enabled: false },
                    wordWrap: 'on',
                    lineNumbers: 'on',
                    folding: true,
                    renderWhitespace: 'selection',
                    scrollBeyondLastLine: false,
                  }}
                />
              </EditorContainer>
            </Box>
          )}

          {renderTabPanel(1, 1,
            <Box p={2}>
              <Typography variant="h6" gutterBottom>Version History</Typography>
              {selectedPrompt ? (
                <Typography>History for {selectedPrompt.prompt_id}</Typography>
              ) : (
                <Typography color="textSecondary">Select a prompt to view history</Typography>
              )}
            </Box>
          )}

          {renderTabPanel(2, 2,
            <Box p={2}>
              <Typography variant="h6" gutterBottom>Compare Versions</Typography>
              <Typography color="textSecondary">Version comparison coming soon...</Typography>
            </Box>
          )}

          {renderTabPanel(3, 3,
            <Box p={2}>
              <Typography variant="h6" gutterBottom>Analytics</Typography>
              <Typography color="textSecondary">Performance analytics coming soon...</Typography>
            </Box>
          )}
        </MainEditor>

        {/* Right Sidebar - Metrics & Tools */}
        <MetricsPanel elevation={1}>
          <Typography variant="h6" gutterBottom>
            Insights & Tools
          </Typography>

          {renderPerformanceMetrics()}

          <Divider />

          {renderABTestStatus()}

          <Divider />

          {renderBranchVisualization()}
        </MetricsPanel>
      </ContentArea>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ m: 2 }}>
          {error}
        </Alert>
      )}

      {/* Dialogs would be implemented here */}
      {/* CreatePromptDialog, BranchDialog, MergeDialog, ABTestDialog, etc. */}
    </DashboardContainer>
  );
};
