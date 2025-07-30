import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, CircularProgress } from '@mui/material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Process: React.FC = () => {
  const [videoPath, setVideoPath] = useState('');
  const [model, setModel] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const { sessionId, setSessionId } = useAppContext();

  const handleProcess = async () => {
    if (!videoPath.trim() && !sessionId) return;

    setProcessing(true);
    setError(null);

    try {
      const response = await apiService.processVideo({ 
        video_path: videoPath || undefined, 
        model 
      });
      setResult(response);
      if (response.session_id) {
        setSessionId(response.session_id);
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Processing failed');
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
        {sessionId && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Using current session: {sessionId}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Video Path (optional if using current session)"
          placeholder="Enter video file path..."
          value={videoPath}
          onChange={(e) => setVideoPath(e.target.value)}
          sx={{ mb: 3 }}
          disabled={!!sessionId}
        />

        <TextField
          fullWidth
          label="AI Model (optional)"
          placeholder="e.g., gpt-4, claude-3"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          sx={{ mb: 3 }}
        />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleProcess}
            disabled={(!videoPath.trim() && !sessionId) || processing}
            startIcon={processing ? <CircularProgress size={20} /> : null}
          >
            {processing ? 'Processing...' : 'Process Video'}
          </Button>
        </Box>
      </Paper>

      {result && (
        <Paper sx={{ p: 4, mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            Processing Results
          </Typography>
          
          {result.final_video && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Final Video
              </Typography>
              <video
                controls
                style={{ width: '100%', maxWidth: '800px' }}
                src={`http://localhost:8000/file/${result.final_video}`}
              />
            </Box>
          )}

          {result.plan && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Processing Plan
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'grey.100' }}>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                  {JSON.stringify(result.plan, null, 2)}
                </pre>
              </Paper>
            </Box>
          )}

          {result.coverage_percentage !== undefined && (
            <Typography variant="body1" color="text.secondary">
              Coverage: {result.coverage_percentage}%
            </Typography>
          )}

          {result.scene_count !== undefined && (
            <Typography variant="body1" color="text.secondary">
              Scenes: {result.scene_count}
            </Typography>
          )}
        </Paper>
      )}
    </Container>
  );
};

export default Process;