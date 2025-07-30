import React, { useEffect } from 'react';
import {
  Box,
  Typography,
  Container,
  Chip,
  Link,
  Grid,
} from '@mui/material';
import { useAppContext } from '../../context/AppContext';
import ApiService from '../../services/api';

const Footer: React.FC = () => {
  const { state, dispatch } = useAppContext();

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        dispatch({ type: 'SET_API_STATUS', payload: 'checking' });
        await ApiService.getHealth();
        dispatch({ type: 'SET_API_STATUS', payload: 'online' });
      } catch (error) {
        dispatch({ type: 'SET_API_STATUS', payload: 'offline' });
      }
    };

    checkApiStatus();
    const interval = setInterval(checkApiStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [dispatch]);

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
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) =>
          theme.palette.mode === 'light'
            ? theme.palette.grey[200]
            : theme.palette.grey[800],
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="body2" color="text.secondary">
              © 2025 AI Video Editor. Built with React & FastAPI.
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', justifyContent: { xs: 'flex-start', md: 'flex-end' }, gap: 2, alignItems: 'center' }}>
              <Chip
                label={`Backend: ${state.apiStatus}`}
                color={getStatusColor(state.apiStatus) as any}
                size="small"
              />
              
              {state.currentSessionId && (
                <Chip
                  label={`Session: ${state.currentSessionId}`}
                  variant="outlined"
                  size="small"
                />
              )}
              
              <Link
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener"
                color="inherit"
                underline="hover"
              >
                API Docs
              </Link>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default Footer;