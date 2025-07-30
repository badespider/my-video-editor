import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, MenuItem } from '@mui/material';
import { Settings } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAppContext } from '../context/AppContext';

const Process: React.FC = () => {
  const navigate = useNavigate();
  const { sessionId, setSessionId } = useAppContext();
  const [inputSessionId, setInputSessionId] = useState('');
  const [model, setModel] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const currentSessionId = sessionId || inputSessionId;

  const handleProcess = async () => {
    if (!currentSessionId) {
      setError('Please enter a session ID');
      return;
    }

    setProcessing(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiService.processVideo({
        video_path: currentSessionId,
        model: model || undefined
      });

      setResult(response);
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process video');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Process Video
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        {!sessionId && (
          <TextField
            fullWidth
            label="Session ID"
            placeholder="Enter session ID of uploaded video..."
            value={inputSessionId}
            onChange={(e) => setInputSessionId(e.target.value)}
            sx={{ mb: 3 }}
          />
        )}

        {sessionId && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Processing video from session: {sessionId}
          </Alert>
        )}

        <TextField
          select
          label="AI Model (Optional)"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          sx={{ mb: 3, minWidth: 200 }}
        >
          <MenuItem value="">Default</MenuItem>
          <MenuItem value="gpt-4">GPT-4</MenuItem>
          <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
        </TextField>

        <Box sx={{ mb: 3 }}>
          <Button
            variant="contained"
            size="large"
            startIcon={<Settings />}
            onClick={handleProcess}
            disabled={processing || !currentSessionId}
          >
            {processing ? 'Processing Video...' : 'Process Video'}
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {result && (
          <Paper sx={{ p: 3, backgroundColor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom>
              Processing Results
            </Typography>
            
            {result.final_video && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Processed Video
                </Typography>
                <video
                  controls
                  style={{ width: '100%', maxWidth: 600 }}
                  src={apiService.getFile(result.final_video)}
                >
                  Your browser does not support the video tag.
                </video>
              </Box>
            )}

            {result.plan && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Processing Plan
                </Typography>
                <Paper sx={{ p: 2, backgroundColor: 'background.paper' }}>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                    {JSON.stringify(result.plan, null, 2)}
                  </pre>
                </Paper>
              </Box>
            )}

            {result.coverage_percentage !== undefined && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Coverage: {result.coverage_percentage}%
              </Typography>
            )}

            {result.scene_count !== undefined && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Scenes: {result.scene_count}
              </Typography>
            )}

            <Box sx={{ mt: 3 }}>
              <Button
                variant="outlined"
                onClick={() => navigate('/edit')}
                sx={{ mr: 2 }}
              >
                Edit Video
              </Button>
              <Button
                variant="outlined"
                onClick={() => navigate('/analyze')}
              >
                Analyze Video
              </Button>
            </Box>
          </Paper>
        )}
      </Paper>
    </Container>
  );
};

export default Process;