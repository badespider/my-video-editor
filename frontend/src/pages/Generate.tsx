import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, CircularProgress } from '@mui/material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Generate: React.FC = () => {
  const [script, setScript] = useState('');
  const [model, setModel] = useState('');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const { setSessionId } = useAppContext();

  const handleGenerate = async () => {
    if (!script.trim()) return;

    setGenerating(true);
    setError(null);

    try {
      const response = await apiService.generateVideo({ script, model });
      setResult(response);
      if (response.session_id) {
        setSessionId(response.session_id);
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Generate Video from Script
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        <TextField
          fullWidth
          multiline
          rows={8}
          label="Video Script"
          placeholder="Enter your video script here..."
          value={script}
          onChange={(e) => setScript(e.target.value)}
          sx={{ mb: 3 }}
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
            onClick={handleGenerate}
            disabled={!script.trim() || generating}
            startIcon={generating ? <CircularProgress size={20} /> : null}
          >
            {generating ? 'Generating...' : 'Generate Video'}
          </Button>
        </Box>
      </Paper>

      {result && (
        <Paper sx={{ p: 4, mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            Generation Results
          </Typography>
          
          {result.clips && result.clips.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Generated Clips ({result.clips.length})
              </Typography>
              <Box sx={{ display: 'grid', gap: 2 }}>
                {result.clips.map((clip: any, index: number) => (
                  <Paper key={index} sx={{ p: 2 }}>
                    <Typography variant="subtitle1">
                      Clip {index + 1}: {clip.description || 'No description'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Duration: {clip.duration || 'Unknown'}s
                    </Typography>
                  </Paper>
                ))}
              </Box>
            </Box>
          )}

          {result.narrations && result.narrations.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Narration
              </Typography>
              {result.narrations.map((narration: any, index: number) => (
                <Paper key={index} sx={{ p: 2, mb: 1 }}>
                  <Typography variant="body1">
                    {narration.text || narration}
                  </Typography>
                </Paper>
              ))}
            </Box>
          )}

          {result.total_duration && (
            <Typography variant="body1" color="text.secondary">
              Total Duration: {result.total_duration}s
            </Typography>
          )}
        </Paper>
      )}
    </Container>
  );
};

export default Generate;