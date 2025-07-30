import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, MenuItem } from '@mui/material';
import { PlayArrow } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAppContext } from '../context/AppContext';

const Generate: React.FC = () => {
  const navigate = useNavigate();
  const { setSessionId } = useAppContext();
  const [script, setScript] = useState('');
  const [model, setModel] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async () => {
    if (!script.trim()) {
      setError('Please enter a script');
      return;
    }

    setGenerating(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiService.generateVideo({
        script: script.trim(),
        model: model || undefined
      });

      setResult(response);
      if (response.session_id) {
        setSessionId(response.session_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate video');
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
          placeholder="Enter your video script here... Describe the scenes, narration, and visual elements you want in your video."
          value={script}
          onChange={(e) => setScript(e.target.value)}
          sx={{ mb: 3 }}
        />

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
            startIcon={<PlayArrow />}
            onClick={handleGenerate}
            disabled={generating || !script.trim()}
          >
            {generating ? 'Generating Video...' : 'Generate Video'}
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
              Generation Results
            </Typography>
            
            {result.clips && result.clips.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Generated Clips ({result.clips.length})
                </Typography>
                <Box sx={{ display: 'grid', gap: 2 }}>
                  {result.clips.map((clip: any, index: number) => (
                    <Paper key={index} sx={{ p: 2 }}>
                      <Typography variant="body2">
                        <strong>Clip {index + 1}:</strong> {clip.description || clip.prompt || 'No description'}
                      </Typography>
                      {clip.duration && (
                        <Typography variant="caption" color="text.secondary">
                          Duration: {clip.duration}s
                        </Typography>
                      )}
                    </Paper>
                  ))}
                </Box>
              </Box>
            )}

            {result.narrations && result.narrations.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Narration
                </Typography>
                {result.narrations.map((narration: any, index: number) => (
                  <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                    {narration.text || narration}
                  </Typography>
                ))}
              </Box>
            )}

            {result.total_duration && (
              <Typography variant="body2" color="text.secondary">
                Total Duration: {result.total_duration}s
              </Typography>
            )}

            {result.session_id && (
              <Box sx={{ mt: 3 }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/preview')}
                >
                  Preview Generated Video
                </Button>
              </Box>
            )}
          </Paper>
        )}
      </Paper>
    </Container>
  );
};

export default Generate;