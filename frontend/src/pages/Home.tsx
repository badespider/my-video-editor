import React, { useEffect, useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Paper,
} from '@mui/material';
import {
  CloudUpload,
  VideoLibrary,
  Analytics,
  Edit,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ApiService from '../services/api';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import ErrorAlert from '../components/Common/ErrorAlert';

const Home: React.FC = () => {
  const navigate = useNavigate();
  const [welcomeMessage, setWelcomeMessage] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWelcomeMessage = async () => {
      try {
        setLoading(true);
        const response = await ApiService.getRoot();
        setWelcomeMessage(response.message);
      } catch (err) {
        setError('Failed to connect to the API server');
        console.error('Failed to fetch welcome message:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchWelcomeMessage();
  }, []);

  const features = [
    {
      title: 'Upload Video',
      description: 'Upload your video files for AI-powered editing and analysis',
      icon: <CloudUpload sx={{ fontSize: 40 }} />,
      action: () => navigate('/upload'),
      color: '#1976d2',
    },
    {
      title: 'Generate Video',
      description: 'Create videos from text scripts using AI technology',
      icon: <VideoLibrary sx={{ fontSize: 40 }} />,
      action: () => navigate('/generate'),
      color: '#388e3c',
    },
    {
      title: 'AI Analysis',
      description: 'Get detailed insights and analysis of your video content',
      icon: <Analytics sx={{ fontSize: 40 }} />,
      action: () => navigate('/analyze'),
      color: '#f57c00',
    },
    {
      title: 'Edit Session',
      description: 'Real-time video editing with AI assistance',
      icon: <Edit sx={{ fontSize: 40 }} />,
      action: () => navigate('/edit'),
      color: '#7b1fa2',
    },
  ];

  if (loading) {
    return <LoadingSpinner message="Connecting to API server..." />;
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {error && <ErrorAlert error={error} onClose={() => setError(null)} />}
      
      {/* Hero Section */}
      <Paper
        elevation={3}
        sx={{
          p: 6,
          mb: 6,
          textAlign: 'center',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
        }}
      >
        <Typography variant="h2" component="h1" gutterBottom>
          AI Video Creation Tool
        </Typography>
        <Typography variant="h5" component="h2" gutterBottom sx={{ opacity: 0.9 }}>
          {welcomeMessage || 'Transform your videos with artificial intelligence'}
        </Typography>
        <Typography variant="body1" sx={{ mb: 4, opacity: 0.8 }}>
          Upload videos, generate content from scripts, and edit with real-time AI assistance.
          Experience the future of video creation.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<CloudUpload />}
            onClick={() => navigate('/upload')}
            sx={{
              bgcolor: 'rgba(255, 255, 255, 0.2)',
              '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.3)' },
            }}
          >
            Upload Video
          </Button>
          <Button
            variant="outlined"
            size="large"
            startIcon={<VideoLibrary />}
            onClick={() => navigate('/generate')}
            sx={{
              borderColor: 'white',
              color: 'white',
              '&:hover': { borderColor: 'white', bgcolor: 'rgba(255, 255, 255, 0.1)' },
            }}
          >
            Generate Video
          </Button>
        </Box>
      </Paper>

      {/* Features Grid */}
      <Typography variant="h4" component="h2" gutterBottom textAlign="center" sx={{ mb: 4 }}>
        Features
      </Typography>
      
      <Grid container spacing={4}>
        {features.map((feature, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ color: feature.color, mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography variant="h6" component="h3" gutterBottom>
                  {feature.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {feature.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button
                  size="small"
                  variant="contained"
                  onClick={feature.action}
                  sx={{ bgcolor: feature.color }}
                >
                  Get Started
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Quick Stats */}
      <Box sx={{ mt: 6, textAlign: 'center' }}>
        <Typography variant="h5" gutterBottom>
          Powered by Advanced AI
        </Typography>
        <Grid container spacing={4} sx={{ mt: 2 }}>
          <Grid item xs={12} md={4}>
            <Typography variant="h3" color="primary">
              AI
            </Typography>
            <Typography variant="body1">
              Intelligent video analysis and editing
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="h3" color="primary">
              Real-time
            </Typography>
            <Typography variant="body1">
              Live preview and instant feedback
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="h3" color="primary">
              Professional
            </Typography>
            <Typography variant="body1">
              Studio-quality results
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default Home;