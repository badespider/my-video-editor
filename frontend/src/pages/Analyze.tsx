import React, { useState } from 'react';
import { Container, Typography, TextField, Button, Box, Paper, Alert, Switch, FormControlLabel } from '@mui/material';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Analyze: React.FC = () => {
  const [inputSessionId, setInputSessionId] = useState('');
  const [detailed, setDetailed] = useState(false);
  const [preferences, setPreferences] = useState('{}');
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const { sessionId } = useAppContext();

  const currentSessionId = sessionId || inputSessionId;

  const handleAnalyze = async () => {
    if (!currentSessionId) return;

    setAnalyzing(true);
    setError(null);

    try {
      let preferencesObj = {};
      try {
        preferencesObj = JSON.parse(preferences);
      } catch (e) {
        // Use empty object if JSON is invalid
      }

      const response = await apiService.analyzeVideo(currentSessionId, {
        detailed,
        preferences: preferencesObj
      });
      setAnalysisResult(response);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Analysis failed');
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
      setError(null);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to get suggestions');
    }
  };

  const handleOptimize = async () => {
    if (!currentSessionId) return;

    try {
      const response = await apiService.optimizeVideo(currentSessionId, {
        target_platform: 'youtube',
        quality_level: 'high'
      });
      setAnalysisResult(response);
      setError(null);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Optimization failed');
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
            placeholder="Enter session ID to analyze..."
            value={inputSessionId}
            onChange={(e) => setInputSessionId(e.target.value)}
            sx={{ mb: 3 }}
          />
        )}

        {sessionId && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Analyzing session: {sessionId}
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

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
          <Button
            variant="contained"
            onClick={handleAnalyze}
            disabled={!currentSessionId || analyzing}
          >
            {analyzing ? 'Analyzing...' : 'Analyze Video'}
          </Button>
          <Button
            variant="outlined"
            onClick={handleGetSuggestions}
            disabled={!currentSessionId}
          >
            Get Suggestions
          </Button>
          <Button
            variant="outlined"
            onClick={handleOptimize}
            disabled={!currentSessionId}
          >
            Optimize
          </Button>
        </Box>
      </Paper>

      {analysisResult && (
        <Paper sx={{ p: 4, mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            Analysis Results
          </Typography>
          
          {analysisResult.scenes && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Scenes ({analysisResult.scenes.length})
              </Typography>
              <Box sx={{ display: 'grid', gap: 2 }}>
                {analysisResult.scenes.map((scene: any, index: number) => (
                  <Paper key={index} sx={{ p: 2 }}>
                    <Typography variant="subtitle1">
                      Scene {index + 1}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {scene.description || 'No description available'}
                    </Typography>
                    {scene.timestamp && (
                      <Typography variant="caption" display="block">
                        Time: {scene.timestamp}
                      </Typography>
                    )}
                  </Paper>
                ))}
              </Box>
            </Box>
          )}

          {analysisResult.emotional_arc && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Emotional Arc
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'grey.100' }}>
                <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>
                  {JSON.stringify(analysisResult.emotional_arc, null, 2)}
                </pre>
              </Paper>
            </Box>
          )}

          {analysisResult.insights && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Insights
              </Typography>
              <Paper sx={{ p: 2 }}>
                <Typography variant="body1">
                  {analysisResult.insights}
                </Typography>
              </Paper>
            </Box>
          )}
        </Paper>
      )}

      {suggestions && (
        <Paper sx={{ p: 4, mt: 3 }}>
          <Typography variant="h5" gutterBottom>
            AI Suggestions
          </Typography>
          
          {suggestions.suggestions && suggestions.suggestions.length > 0 && (
            <Box sx={{ display: 'grid', gap: 2 }}>
              {suggestions.suggestions.map((suggestion: any, index: number) => (
                <Paper key={index} sx={{ p: 2, border: '1px solid #e0e0e0' }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {suggestion.title || `Suggestion ${index + 1}`}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {suggestion.description || suggestion}
                  </Typography>
                  {suggestion.confidence && (
                    <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                      Confidence: {Math.round(suggestion.confidence * 100)}%
                    </Typography>
                  )}
                </Paper>
              ))}
            </Box>
          )}
        </Paper>
      )}
    </Container>
  );
};

export default Analyze;