import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Avatar,
  Tabs,
  Tab,
  Alert,
  Tooltip,
  FormControlLabel,
  Checkbox,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Notifications as NotificationsIcon,
  Key as KeyIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  AdminPanelSettings as AdminIcon,
  Group as GroupIcon,
  Dashboard as DashboardIcon,
  VpnKey as VpnKeyIcon,
} from '@mui/icons-material';

interface UserConfig {
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  display_name?: string;
  avatar_url?: string;
  access_level: 'viewer' | 'analyst' | 'developer' | 'admin' | 'owner';
  feature_access: string[];
  department?: string;
  team?: string;
  is_active: boolean;
  is_verified: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`user-tabpanel-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const FEATURE_DESCRIPTIONS = {
  brain_view: 'View knowledge brain content',
  brain_edit: 'Edit knowledge brain schemas and data',
  agents_view: 'View AI agents',
  agents_create: 'Create new AI agents',
  agents_edit: 'Edit existing AI agents',
  integrations_view: 'View integrations',
  integrations_manage: 'Manage integration settings',
  analytics_view: 'View analytics dashboards',
  analytics_export: 'Export analytics data',
  workflows_view: 'View workflows',
  workflows_create: 'Create new workflows',
  workflows_execute: 'Execute workflows',
  voice_access: 'Access voice interface',
  api_access: 'API access',
  billing_view: 'View billing information',
  billing_manage: 'Manage billing settings',
  users_view: 'View user list',
  users_manage: 'Manage users',
  settings_view: 'View settings',
  settings_manage: 'Manage system settings',
};

const ACCESS_LEVEL_COLORS = {
  viewer: 'default',
  analyst: 'primary',
  developer: 'secondary',
  admin: 'warning',
  owner: 'error',
} as const;

const ACCESS_LEVEL_ICONS = {
  viewer: <PersonIcon />,
  analyst: <DashboardIcon />,
  developer: <SettingsIcon />,
  admin: <AdminIcon />,
  owner: <SecurityIcon />,
};

export default function UserConfiguration() {
  const [users, setUsers] = useState<UserConfig[]>([]);
  const [selectedUser, setSelectedUser] = useState<UserConfig | null>(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [isCreating, setIsCreating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentUserEmail, setCurrentUserEmail] = useState('lynn@sophia-intel.ai');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAccessLevel, setFilterAccessLevel] = useState<string>('all');
  const [filterDepartment, setFilterDepartment] = useState<string>('all');
  
  // Form state for new/edit user
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    access_level: 'viewer' as const,
    department: '',
    team: '',
    feature_access: [] as string[],
  });

  const isCEO = currentUserEmail === 'lynn@sophia-intel.ai';

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/users', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = () => {
    setIsCreating(true);
    setFormData({
      email: '',
      first_name: '',
      last_name: '',
      access_level: 'viewer',
      department: '',
      team: '',
      feature_access: [],
    });
    setOpenDialog(true);
  };

  const handleEditUser = (user: UserConfig) => {
    setIsCreating(false);
    setSelectedUser(user);
    setFormData({
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      access_level: user.access_level,
      department: user.department || '',
      team: user.team || '',
      feature_access: user.feature_access,
    });
    setOpenDialog(true);
  };

  const handleSaveUser = async () => {
    try {
      const endpoint = isCreating ? '/api/users' : `/api/users/${selectedUser?.user_id}`;
      const method = isCreating ? 'POST' : 'PATCH';
      
      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify(formData),
      });
      
      if (response.ok) {
        fetchUsers();
        setOpenDialog(false);
      }
    } catch (error) {
      console.error('Failed to save user:', error);
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return;
    
    try {
      const response = await fetch(`/api/users/${userId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
        },
      });
      
      if (response.ok) {
        fetchUsers();
      }
    } catch (error) {
      console.error('Failed to delete user:', error);
    }
  };

  const handleFeatureToggle = (feature: string) => {
    setFormData(prev => ({
      ...prev,
      feature_access: prev.feature_access.includes(feature)
        ? prev.feature_access.filter(f => f !== feature)
        : [...prev.feature_access, feature],
    }));
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = 
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.last_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesAccessLevel = 
      filterAccessLevel === 'all' || user.access_level === filterAccessLevel;
    
    const matchesDepartment = 
      filterDepartment === 'all' || user.department === filterDepartment;
    
    return matchesSearch && matchesAccessLevel && matchesDepartment;
  });

  const departments = ['all', ...new Set(users.map(u => u.department).filter(Boolean))];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          User Configuration
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateUser}
        >
          Add User
        </Button>
      </Box>

      {/* CEO Alert for Schema Changes */}
      {isCEO && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            As CEO, you have exclusive access to schema changes. Access the Brain Controls to manage data structures.
          </Typography>
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size="small"
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Access Level</InputLabel>
              <Select
                value={filterAccessLevel}
                onChange={(e) => setFilterAccessLevel(e.target.value)}
                label="Access Level"
              >
                <MenuItem value="all">All Levels</MenuItem>
                <MenuItem value="viewer">Viewer</MenuItem>
                <MenuItem value="analyst">Analyst</MenuItem>
                <MenuItem value="developer">Developer</MenuItem>
                <MenuItem value="admin">Admin</MenuItem>
                {isCEO && <MenuItem value="owner">Owner</MenuItem>}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Department</InputLabel>
              <Select
                value={filterDepartment}
                onChange={(e) => setFilterDepartment(e.target.value)}
                label="Department"
              >
                {departments.map(dept => (
                  <MenuItem key={dept} value={dept}>
                    {dept === 'all' ? 'All Departments' : dept}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="text.secondary">
              {filteredUsers.length} users
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>User</TableCell>
              <TableCell>Access Level</TableCell>
              <TableCell>Department</TableCell>
              <TableCell>Team</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredUsers.map((user) => (
              <TableRow key={user.user_id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Avatar src={user.avatar_url}>
                      {user.first_name[0]}{user.last_name[0]}
                    </Avatar>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">
                        {user.first_name} {user.last_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {user.email}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip
                    icon={ACCESS_LEVEL_ICONS[user.access_level]}
                    label={user.access_level.toUpperCase()}
                    color={ACCESS_LEVEL_COLORS[user.access_level]}
                    size="small"
                  />
                </TableCell>
                <TableCell>{user.department || '-'}</TableCell>
                <TableCell>{user.team || '-'}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {user.is_active ? (
                      <Chip
                        icon={<CheckCircleIcon />}
                        label="Active"
                        color="success"
                        size="small"
                      />
                    ) : (
                      <Chip
                        icon={<BlockIcon />}
                        label="Inactive"
                        color="default"
                        size="small"
                      />
                    )}
                    {user.is_verified && (
                      <Tooltip title="Verified">
                        <CheckCircleIcon color="primary" fontSize="small" />
                      </Tooltip>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  {user.last_login
                    ? new Date(user.last_login).toLocaleDateString()
                    : 'Never'
                  }
                </TableCell>
                <TableCell align="right">
                  <IconButton
                    size="small"
                    onClick={() => handleEditUser(user)}
                  >
                    <EditIcon />
                  </IconButton>
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteUser(user.user_id)}
                    disabled={user.email === currentUserEmail}
                  >
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create/Edit Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {isCreating ? 'Create New User' : 'Edit User'}
        </DialogTitle>
        <DialogContent>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
            <Tab label="Basic Info" />
            <Tab label="Permissions" />
            <Tab label="Features" />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!isCreating}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Department"
                  value={formData.department}
                  onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Team"
                  value={formData.team}
                  onChange={(e) => setFormData({ ...formData, team: e.target.value })}
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Access Level</InputLabel>
              <Select
                value={formData.access_level}
                onChange={(e) => setFormData({ ...formData, access_level: e.target.value as any })}
                label="Access Level"
              >
                <MenuItem value="viewer">Viewer - Read only access</MenuItem>
                <MenuItem value="analyst">Analyst - Run analyses and queries</MenuItem>
                <MenuItem value="developer">Developer - Modify agents and workflows</MenuItem>
                {isCEO && (
                  <>
                    <MenuItem value="admin">Admin - System administration</MenuItem>
                    <MenuItem value="owner">Owner - Full control</MenuItem>
                  </>
                )}
              </Select>
            </FormControl>

            {formData.access_level === 'admin' || formData.access_level === 'owner' ? (
              <Alert severity="warning">
                This access level grants elevated privileges. Only CEO can assign admin/owner roles.
              </Alert>
            ) : null}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="subtitle2" gutterBottom>
              Select features this user can access:
            </Typography>
            <Grid container spacing={1}>
              {Object.entries(FEATURE_DESCRIPTIONS).map(([key, description]) => (
                <Grid item xs={12} md={6} key={key}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.feature_access.includes(key)}
                        onChange={() => handleFeatureToggle(key)}
                        disabled={key === 'schema_changes' && !isCEO}
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">{key.replace(/_/g, ' ').toUpperCase()}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {description}
                        </Typography>
                        {key === 'brain_edit' && (
                          <Typography variant="caption" color="warning.main" display="block">
                            (Schema changes CEO only)
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                </Grid>
              ))}
            </Grid>
          </TabPanel>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveUser} variant="contained">
            {isCreating ? 'Create' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}