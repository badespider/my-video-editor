import React, { useEffect, useState } from 'react';
import { Container, Typography, Button, Box, Paper } from '@mui/material';
import { Link } from 'react-router-dom';
import { apiService } from '../services/api';

const Home: React.FC = () => {
  const [welcomeMessage, setWelcomeMessage] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWelcomeMessage = async () => {
      try {
        const response = await apiService.getRoot();
        setWelcomeMessage(response.message || 'Welcome to AI Video Editor');
      } catch (error) {
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
          {loading ? 'Loading...' : welcomeMessage}
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph sx={{ maxWidth: 600, mx: 'auto' }}>
          Create, edit, and enhance your videos with the power of artificial intelligence.
          Upload your existing videos or generate new ones from scripts.
        </Typography>
        <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant="contained"
            size="large"
            component={Link}
            to="/upload"
          >
            Upload Video
          </Button>
          <Button
            variant="outlined"
            size="large"
            component={Link}
            to="/generate"
          >
            Generate Video
          </Button>
        </Box>
      </Box>

      <Box sx={{ mt: 8 }}>
        <Typography variant="h4" component="h2" gutterBottom textAlign="center">
          Features
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 3, mt: 4 }}>
          {[
            {
              title: 'Upload & Process',
              description: 'Upload your videos and let AI analyze and process them automatically.',
              link: '/upload'
            },
            {
              title: 'Generate from Script',
              description: 'Create videos from text scripts using advanced AI models.',
              link: '/generate'
            },
            {
              title: 'Real-time Editing',
              description: 'Edit your videos with real-time preview and AI assistance.',
              link: '/edit'
            },
            {
              title: 'AI Analysis',
              description: 'Get detailed insights and suggestions for your video content.',
              link: '/analyze'
            }
          ].map((feature, index) => (
            <Paper key={index} sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" gutterBottom>
                {feature.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {feature.description}
              </Typography>
              <Button variant="text" component={Link} to={feature.link}>
                Learn More
              </Button>
            </Paper>
          ))}
        </Box>
      </Box>
    </Container>
  );
};

export default Home;