import React, { useEffect } from 'react';
import { Box, Typography, Chip } from '@mui/material';
import { useAppContext } from '../../context/AppContext';
import { apiService } from '../../services/api';

const Footer: React.FC = () => {
  const { sessionId, apiStatus, setApiStatus } = useAppContext();

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await apiService.getRoot();
        setApiStatus('Connected');
      } catch (error) {
        setApiStatus('Disconnected');
      }
    };

    checkApiStatus();
    const interval = setInterval(checkApiStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [setApiStatus]);

  return (
    <Box
      component="footer"
      sx={{
        py: 2,
        px: 3,
        mt: 'auto',
        backgroundColor: 'background.paper',
        borderTop: 1,
        borderColor: 'divider',
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          AI Video Editor © 2024
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Chip
            label={`API: ${apiStatus}`}
            color={apiStatus === 'Connected' ? 'success' : 'error'}
            size="small"
          />
          {sessionId && (
            <Chip
              label={`Session: ${sessionId.substring(0, 8)}...`}
              color="primary"
              size="small"
            />
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default Footer;