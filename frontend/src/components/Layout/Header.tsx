import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import { useAppContext } from '../../context/AppContext';

const Header: React.FC = () => {
  const location = useLocation();
  const { toggleTheme, theme } = useAppContext();

  const navItems = [
    { label: 'Home', path: '/' },
    { label: 'Upload', path: '/upload' },
    { label: 'Generate', path: '/generate' },
    { label: 'Process', path: '/process' },
    { label: 'Edit', path: '/edit' },
    { label: 'Preview', path: '/preview' },
    { label: 'Analyze', path: '/analyze' },
  ];

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI Video Editor
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              color="inherit"
              component={Link}
              to={item.path}
              variant={location.pathname === item.path ? 'outlined' : 'text'}
            >
              {item.label}
            </Button>
          ))}
          <Button color="inherit" onClick={toggleTheme}>
            {theme === 'light' ? '🌙' : '☀️'}
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;