import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  FormControlLabel,
  Switch,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { Analytics, ExpandMore, TrendingUp, Lightbulb, Tune } from '@mui/icons-material';
import { useAppContext } from '../context/AppContext';
import ApiService from '../services/api';
import ErrorAlert from '../components/Common/ErrorAlert';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const Analyze: React.FC = () => {
  const { state } = useAppContext();
  const [sessionId, setSessionId] = useState(state.currentSessionId || '');
  const [detailed, setDetailed] = useState(true);
  const [preferences, setPreferences] = useState('{}');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [suggestionsResult, setSuggestionsResult] = useState<any>(null);
  const [optimizationResult, setOptimizationResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!sessionId) {
      setError('Please enter a session ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let parsedPreferences = {};
      try {
        parsedPreferences = JSON.parse(preferences);
      } catch {
        // Use empty object if JSON is invalid
      }

      const response = await ApiService.analyzeVideo(sessionId, {
        detailed,
        preferences: parsedPreferences,
      });

      setAnalysisResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGetSuggestions = async () => {
    if (!sessionId) {
      setError('Please enter a session ID');
      return;
    }

    try {
      setLoading(true);
      const response = await ApiService.getSuggestions(sessionId, {
        max_suggestions: 8,
      });
      setSuggestionsResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get suggestions');
    } finally {
      setLoading(false);
    }
  };

  const handleOptimize = async () => {
    if (!sessionId) {
      setError('Please enter a session ID');
      return;
    }

    try {
      setLoading(true);
      const response = await ApiService.optimizeVideo(sessionId, {
        target_platform: 'youtube',
        quality_level: 'high',
      });
      setOptimizationResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const formatEmotionalData = (analysis: any) => {
    if (!analysis?.emotional_arc?.progression) return [];
    
    return analysis.emotional_arc.progression.map((point: any, index: number) => ({
      scene: `Scene ${index + 1}`,
      intensity: point.intensity || 0,
      position: point.position || 0,
    }));
  };

  const formatSceneData = (analysis: any) => {
    if (!analysis?.scenes) return [];
    
    return analysis.scenes.map((scene: any, index: number) => ({
      name: `Scene ${index + 1}`,
      duration: scene.duration || 0,
      score: scene.score || 0,
    }));
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        AI Video Analysis
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Get detailed insights, suggestions, and optimization recommendations for your videos.
      </Typography>

      {error && <ErrorAlert error={error} onClose={() => setError(null)} />}

      <Grid container spacing={4}>
        {/* Analysis Controls */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Settings
              </Typography>
              
              <TextField
                fullWidth
                label="Session ID"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                sx={{ mb: 2 }}
                placeholder="Enter session ID"
              />

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
                rows={4}
                label="Preferences (JSON)"
                value={preferences}
                onChange={(e) => setPreferences(e.target.value)}
                placeholder='{"style": "cinematic", "pace": "moderate"}'
                sx={{ mb: 3 }}
                helperText="Optional JSON object with analysis preferences"
              />

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<Analytics />}
                  onClick={handleAnalyze}
                  disabled={!sessionId || loading}
                  fullWidth
                >
                  Analyze Video
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Lightbulb />}
                  onClick={handleGetSuggestions}
                  disabled={!sessionId || loading}
                  fullWidth
                >
                  Get AI Suggestions
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<Tune />}
                  onClick={handleOptimize}
                  disabled={!sessionId || loading}
                  fullWidth
                >
                  Optimize Video
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={8}>
          {loading && <LoadingSpinner message="Analyzing video with AI..." />}

          {/* Analysis Results */}
          {analysisResult && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                Analysis Results
              </Typography>

              {/* Summary */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Summary
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    {analysisResult.content_type && (
                      <Chip label={`Type: ${analysisResult.content_type}`} color="primary" />
                    )}
                    {analysisResult.mood_analysis?.primary_mood && (
                      <Chip label={`Mood: ${analysisResult.mood_analysis.primary_mood}`} color="secondary" />
                    )}
                    {analysisResult.quality_metrics?.overall_quality && (
                      <Chip label={`Quality: ${(analysisResult.quality_metrics.overall_quality * 100).toFixed(0)}%`} />
                    )}
                  </Box>
                </CardContent>
              </Card>

              {/* Emotional Arc Chart */}
              {analysisResult.emotional_arc && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Emotional Progression
                    </Typography>
                    <Box sx={{ height: 300, width: '100%' }}>
                      <ResponsiveContainer>
                        <LineChart data={formatEmotionalData(analysisResult)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="scene" />
                          <YAxis />
                          <Tooltip />
                          <Line type="monotone" dataKey="intensity" stroke="#1976d2" strokeWidth={2} />
                        </LineChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              )}

              {/* Scene Analysis */}
              {analysisResult.scenes && (
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Scene Breakdown
                    </Typography>
                    <Box sx={{ height: 300, width: '100%' }}>
                      <ResponsiveContainer>
                        <BarChart data={formatSceneData(analysisResult)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="duration" fill="#1976d2" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  </CardContent>
                </Card>
              )}
            </Box>
          )}

          {/* Suggestions Results */}
          {suggestionsResult && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h5" gutterBottom>
                AI Suggestions
              </Typography>

              <Card>
                <CardContent>
                  {suggestionsResult.suggestions?.map((suggestion: any, index: number) => (
                    <Accordion key={index}>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                          <Typography variant="subtitle1">
                            {suggestion.title || `Suggestion ${index + 1}`}
                          </Typography>
                          <Chip 
                            label={suggestion.category || 'general'} 
                            size="small" 
                            color="primary" 
                          />
                          {suggestion.confidence && (
                            <Chip 
                              label={`${(suggestion.confidence * 100).toFixed(0)}%`} 
                              size="small" 
                              variant="outlined" 
                            />
                          )}
                        </Box>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Typography variant="body2">
                          {suggestion.description || 'No description available'}
                        </Typography>
                        {suggestion.parameters && (
                          <Box sx={{ mt: 2 }}>
                            <Typography variant="caption" color="text.secondary">
                              Parameters: {JSON.stringify(suggestion.parameters)}
                            </Typography>
                          </Box>
                        )}
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </CardContent>
              </Card>
            </Box>
          )}

          {/* Optimization Results */}
          {optimizationResult && (
            <Box>
              <Typography variant="h5" gutterBottom>
                Optimization Recommendations
              </Typography>

              <Grid container spacing={2}>
                {/* Technical Optimizations */}
                {optimizationResult.technical_optimizations && (
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Technical Optimizations
                        </Typography>
                        <List dense>
                          {optimizationResult.technical_optimizations.map((opt: any, index: number) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={opt.recommendation}
                                secondary={`${opt.type} - Priority: ${opt.priority}`}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                {/* Content Optimizations */}
                {optimizationResult.content_optimizations && (
                  <Grid item xs={12} md={6}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Content Optimizations
                        </Typography>
                        <List dense>
                          {optimizationResult.content_optimizations.map((opt: any, index: number) => (
                            <ListItem key={index}>
                              <ListItemText
                                primary={opt.recommendation}
                                secondary={`${opt.type} - Priority: ${opt.priority}`}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Analyze;