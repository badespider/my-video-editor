import React, { useState, useEffect } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert } from '@mui/material';
import { PlayArrow, GetApp } from '@mui/icons-material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Preview: React.FC = () => {
  const { sessionId } = useAppContext();
  const [inputSessionId, setInputSessionId] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionInfo, setSessionInfo] = useState<any>(null);

  const currentSessionId = sessionId || inputSessionId;

  const loadPreview = async () => {
    if (!currentSessionId) {
      setError('Please enter a session ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Try to get session info first
      const info = await apiService.getSessionInfo(currentSessionId);
      setSessionInfo(info);

      // Get preview video
      const response = await apiService.getPreview(currentSessionId);
      const blob = response.data;
      const url = URL.createObjectURL(blob);
      setPreviewUrl(url);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load preview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId) {
      loadPreview();
    }
  }, [sessionId]);

  const handleFinalize = async () => {
    if (!currentSessionId) return;

    try {
      const response = await apiService.finalizeVideo(currentSessionId);
      if (response.final_path) {
        // Create download link
        const link = document.createElement('a');
        link.href = apiService.getFile(response.final_path);
        link.download = 'final_video.mp4';
        link.click();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to finalize video');
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Video Preview
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        {!sessionId && (
          <Box sx={{ mb: 3 }}>
            <TextField
              fullWidth
              label="Session ID"
              placeholder="Enter session ID to preview video..."
              value={inputSessionId}
              onChange={(e) => setInputSessionId(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              onClick={loadPreview}
              disabled={loading || !inputSessionId}
            >
              {loading ? 'Loading...' : 'Load Preview'}
            </Button>
          </Box>
        )}

        {sessionId && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Previewing video from session: {sessionId}
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {previewUrl && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Video Preview
            </Typography>
            <video
              controls
              style={{ width: '100%', maxWidth: 800 }}
              src={previewUrl}
            >
              Your browser does not support the video tag.
            </video>
            
            <Box sx={{ mt: 2 }}>
              <Button
                variant="contained"
                startIcon={<GetApp />}
                onClick={handleFinalize}
                sx={{ mr: 2 }}
              >
                Finalize & Download
              </Button>
            </Box>
          </Box>
        )}

        {sessionInfo && (
          <Paper sx={{ p: 3, backgroundColor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom>
              Session Information
            </Typography>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
              {JSON.stringify(sessionInfo, null, 2)}
            </pre>
          </Paper>
        )}
      </Paper>
    </Container>
  );
};

export default Preview;