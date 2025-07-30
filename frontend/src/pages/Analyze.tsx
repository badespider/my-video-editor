import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, Switch, FormControlLabel } from '@mui/material';
import { Analytics, Lightbulb, Tune } from '@mui/icons-material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Analyze: React.FC = () => {
  const { sessionId } = useAppContext();
  const [inputSessionId, setInputSessionId] = useState('');
  const [detailed, setDetailed] = useState(false);
  const [preferences, setPreferences] = useState('{}');
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<any>(null);

  const currentSessionId = sessionId || inputSessionId;

  const handleAnalyze = async () => {
    if (!currentSessionId) {
      setError('Please enter a session ID');
      return;
    }

    setAnalyzing(true);
    setError(null);
    setAnalysis(null);

    try {
      let prefs = {};
      if (preferences.trim()) {
        prefs = JSON.parse(preferences);
      }

      const response = await apiService.analyzeVideo(currentSessionId, {
        detailed,
        preferences: prefs
      });

      setAnalysis(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze video');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleGetSuggestions = async () => {
    if (!currentSessionId) return;

    try {
      const response = await apiService.getSuggestions(currentSessionId, {
        max_suggestions: 5
      });
      setSuggestions(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get suggestions');
    }
  };

  const handleOptimize = async (platform: string = 'youtube', quality: string = 'high') => {
    if (!currentSessionId) return;

    try {
      const response = await apiService.optimizeVideo(currentSessionId, {
        target_platform: platform,
        quality_level: quality
      });
      
      setAnalysis(prev => ({
        ...prev,
        optimization: response
      }));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to optimize video');
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        AI Video Analysis
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        {!sessionId && (
          <TextField
            fullWidth
            label="Session ID"
            placeholder="Enter session ID to analyze video..."
            value={inputSessionId}
            onChange={(e) => setInputSessionId(e.target.value)}
            sx={{ mb: 3 }}
          />
        )}

        {sessionId && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Analyzing video from session: {sessionId}
          </Alert>
        )}

        <FormControlLabel
          control={
            <Switch
              checked={detailed}
              onChange={(e) => setDetailed(e.target.checked)}
            />
          }
          label="Detailed Analysis"
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          multiline
          rows={3}
          label="Analysis Preferences (JSON)"
          placeholder='{"focus": "emotional_arc", "include_timestamps": true}'
          value={preferences}
          onChange={(e) => setPreferences(e.target.value)}
          sx={{ mb: 3 }}
        />

        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Button
            variant="contained"
            startIcon={<Analytics />}
            onClick={handleAnalyze}
            disabled={analyzing || !currentSessionId}
          >
            {analyzing ? 'Analyzing...' : 'Analyze Video'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<Lightbulb />}
            onClick={handleGetSuggestions}
            disabled={!currentSessionId}
          >
            Get Suggestions
          </Button>
          <Button
            variant="outlined"
            startIcon={<Tune />}
            onClick={() => handleOptimize()}
            disabled={!currentSessionId}
          >
            Optimize for YouTube
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {analysis && (
          <Paper sx={{ p: 3, backgroundColor: 'grey.50', mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Analysis Results
            </Typography>
            
            {analysis.scenes && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Scene Analysis
                </Typography>
                <Box sx={{ display: 'grid', gap: 2 }}>
                  {analysis.scenes.map((scene: any, index: number) => (
                    <Paper key={index} sx={{ p: 2 }}>
                      <Typography variant="body2">
                        <strong>Scene {index + 1}:</strong> {scene.description || 'No description'}
                      </Typography>
                      {scene.timestamp && (
                        <Typography variant="caption" color="text.secondary">
                          Time: {scene.timestamp}
                        </Typography>
                      )}
                    </Paper>
                  ))}
                </Box>
              </Box>
            )}

            {analysis.emotional_arc && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Emotional Arc
                </Typography>
                <Typography variant="body2">
                  {JSON.stringify(analysis.emotional_arc, null, 2)}
                </Typography>
              </Box>
            )}

            {analysis.insights && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  AI Insights
                </Typography>
                {Array.isArray(analysis.insights) ? (
                  analysis.insights.map((insight: string, index: number) => (
                    <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                      • {insight}
                    </Typography>
                  ))
                ) : (
                  <Typography variant="body2">
                    {analysis.insights}
                  </Typography>
                )}
              </Box>
            )}

            {analysis.optimization && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Optimization Results
                </Typography>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                  {JSON.stringify(analysis.optimization, null, 2)}
                </pre>
              </Box>
            )}
          </Paper>
        )}

        {suggestions && (
          <Paper sx={{ p: 3, backgroundColor: 'grey.50' }}>
            <Typography variant="h6" gutterBottom>
              AI Suggestions
            </Typography>
            {suggestions.suggestions && suggestions.suggestions.map((suggestion: any, index: number) => (
              <Paper key={index} sx={{ p: 2, mb: 2 }}>
                <Typography variant="body1" gutterBottom>
                  {suggestion.title || `Suggestion ${index + 1}`}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {suggestion.description || suggestion}
                </Typography>
                {suggestion.confidence && (
                  <Typography variant="caption" color="text.secondary">
                    Confidence: {suggestion.confidence}%
                  </Typography>
                )}
              </Paper>
            ))}
          </Paper>
        )}
      </Paper>
    </Container>
  );
};

export default Analyze;