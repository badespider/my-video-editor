import React, { useState, useEffect } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert } from '@mui/material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Preview: React.FC = () => {
  const [inputSessionId, setInputSessionId] = useState('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [sessionInfo, setSessionInfo] = useState<any>(null);
  const [thumbnailTime, setThumbnailTime] = useState('00:05:00');
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { sessionId } = useAppContext();

  const currentSessionId = sessionId || inputSessionId;

  useEffect(() => {
    if (currentSessionId) {
      loadPreview();
      loadSessionInfo();
    }
  }, [currentSessionId]);

  const loadPreview = async () => {
    if (!currentSessionId) return;

    try {
      setPreviewUrl(`http://localhost:8000/preview/${currentSessionId}`);
      setError(null);
    } catch (error: any) {
      setError('Failed to load preview');
    }
  };

  const loadSessionInfo = async () => {
    if (!currentSessionId) return;

    try {
      const info = await apiService.getSessionInfo(currentSessionId);
      setSessionInfo(info);
    } catch (error: any) {
      console.error('Failed to load session info:', error);
    }
  };

  const generateThumbnail = async () => {
    if (!currentSessionId) return;

    try {
      const response = await apiService.generateThumbnail(currentSessionId, { time: thumbnailTime });
      setThumbnailUrl(`http://localhost:8000/file/${response.thumbnail_path}`);
      setError(null);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to generate thumbnail');
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Video Preview
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        {!sessionId && (
          <TextField
            fullWidth
            label="Session ID"
            placeholder="Enter session ID to preview..."
            value={inputSessionId}
            onChange={(e) => setInputSessionId(e.target.value)}
            sx={{ mb: 3 }}
          />
        )}

        {sessionId && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Previewing session: {sessionId}
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {previewUrl && (
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Video Preview
            </Typography>
            <video
              controls
              style={{ width: '100%', maxWidth: '800px' }}
              src={previewUrl}
            />
          </Box>
        )}

        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Generate Thumbnail
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
            <TextField
              label="Time (HH:MM:SS)"
              value={thumbnailTime}
              onChange={(e) => setThumbnailTime(e.target.value)}
              placeholder="00:05:00"
            />
            <Button
              variant="contained"
              onClick={generateThumbnail}
              disabled={!currentSessionId}
            >
              Generate
            </Button>
          </Box>
          {thumbnailUrl && (
            <img
              src={thumbnailUrl}
              alt="Video thumbnail"
              style={{ maxWidth: '300px', border: '1px solid #ccc' }}
            />
          )}
        </Box>

        {sessionInfo && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Session Information
            </Typography>
            <Paper sx={{ p: 2, backgroundColor: 'grey.100' }}>
              <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                {JSON.stringify(sessionInfo, null, 2)}
              </pre>
            </Paper>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default Preview;