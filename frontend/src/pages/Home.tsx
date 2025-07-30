import React, { useEffect, useState } from 'react';
import { Container, Typography, Button, Box, Paper, Alert } from '@mui/material';
import { VideoLibrary, CloudUpload } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [welcomeMessage, setWelcomeMessage] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWelcomeMessage = async () => {
      try {
        const response = await apiService.getRoot();
        setWelcomeMessage(response.message || 'Welcome to AI Video Editor');
      } catch (err) {
        setError('Failed to connect to the API');
        setWelcomeMessage('Welcome to AI Video Editor');
      } finally {
        setLoading(false);
      }
    };

    fetchWelcomeMessage();
  }, []);

  return (
    <Container maxWidth="lg">
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h2" component="h1" gutterBottom>
          AI Video Creation Tool
        </Typography>
        <Typography variant="h5" color="text.secondary" paragraph>
          Create, edit, and optimize videos with the power of artificial intelligence
        </Typography>

        {error && (
          <Alert severity="warning" sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}>
            {error}
          </Alert>
        )}

        <Paper sx={{ p: 4, mt: 4, maxWidth: 800, mx: 'auto' }}>
          <Typography variant="h6" gutterBottom>
            {loading ? 'Connecting to API...' : welcomeMessage}
          </Typography>
          
          <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', mt: 4 }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<CloudUpload />}
              onClick={() => navigate('/upload')}
              sx={{ minWidth: 200 }}
            >
              Upload Video
            </Button>
            <Button
              variant="outlined"
              size="large"
              startIcon={<VideoLibrary />}
              onClick={() => navigate('/generate')}
              sx={{ minWidth: 200 }}
            >
              Generate Video
            </Button>
          </Box>
        </Paper>

        <Box sx={{ mt: 6, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3 }}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Upload & Process
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Upload your existing videos and let AI analyze and enhance them
            </Typography>
          </Paper>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Generate from Script
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create videos from text scripts using AI-powered generation
            </Typography>
          </Paper>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Real-time Editing
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Edit videos in real-time with WebSocket-powered collaboration
            </Typography>
          </Paper>
        </Box>
      </Box>
    </Container>
  );
};

export default Home;