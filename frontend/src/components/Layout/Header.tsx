import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Home,
  CloudUpload,
  VideoLibrary,
  Edit,
  Preview,
  Analytics,
  Settings,
  Brightness4,
  Brightness7,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { state, dispatch } = useAppContext();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const navigationItems = [
    { label: 'Home', path: '/', icon: <Home /> },
    { label: 'Upload', path: '/upload', icon: <CloudUpload /> },
    { label: 'Generate', path: '/generate', icon: <VideoLibrary /> },
    { label: 'Process', path: '/process', icon: <Settings /> },
    { label: 'Edit', path: '/edit', icon: <Edit /> },
    { label: 'Preview', path: '/preview', icon: <Preview /> },
    { label: 'Analyze', path: '/analyze', icon: <Analytics /> },
  ];

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const toggleTheme = () => {
    dispatch({
      type: 'SET_THEME',
      payload: state.theme === 'light' ? 'dark' : 'light',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      default:
        return 'warning';
    }
  };

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI Video Editor
        </Typography>

        {/* Navigation Items */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1 }}>
          {navigationItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              variant={location.pathname === item.path ? 'outlined' : 'text'}
              sx={{
                borderColor: location.pathname === item.path ? 'white' : 'transparent',
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {/* Mobile Menu */}
        <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
          <IconButton color="inherit" onClick={handleMenuOpen}>
            <Settings />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            {navigationItems.map((item) => (
              <MenuItem
                key={item.path}
                onClick={() => {
                  navigate(item.path);
                  handleMenuClose();
                }}
              >
                {item.icon}
                <Typography sx={{ ml: 1 }}>{item.label}</Typography>
              </MenuItem>
            ))}
          </Menu>
        </Box>

        {/* Theme Toggle */}
        <IconButton color="inherit" onClick={toggleTheme} sx={{ ml: 1 }}>
          {state.theme === 'light' ? <Brightness4 /> : <Brightness7 />}
        </IconButton>

        {/* API Status */}
        <Chip
          label={`API: ${state.apiStatus}`}
          color={getStatusColor(state.apiStatus) as any}
          size="small"
          sx={{ ml: 2 }}
        />

        {/* Session ID */}
        {state.currentSessionId && (
          <Chip
            label={`Session: ${state.currentSessionId.slice(0, 8)}...`}
            variant="outlined"
            size="small"
            sx={{ ml: 1, color: 'white', borderColor: 'white' }}
          />
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;