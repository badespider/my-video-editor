import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Divider,
} from '@mui/material';
import { VideoLibrary, Download, PlayArrow } from '@mui/icons-material';
import ApiService from '../services/api';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import ErrorAlert from '../components/Common/ErrorAlert';
import { VideoResponse } from '../types/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Generate: React.FC = () => {
  const [script, setScript] = useState('');
  const [model, setModel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VideoResponse | null>(null);

  const models = [
    { value: '', label: 'Default' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'grok-4', label: 'Grok-4' },
    { value: 'mock', label: 'Mock (Testing)' },
  ];

  const handleGenerate = async () => {
    if (!script.trim()) {
      setError('Please enter a script');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const response = await ApiService.generateVideo(script, model || undefined);
      setResult(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate video. Please try again.');
      console.error('Generate error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (result) {
      // Create a downloadable JSON file
      const dataStr = JSON.stringify(result, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
      
      const exportFileDefaultName = 'video_plan.json';
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
    }
  };

  const formatTimelineData = (timeline: VideoResponse['timeline']) => {
    return timeline
      .filter(item => item.event === 'clip_start')
      .map(item => ({
        name: `Clip ${item.clip_id}`,
        duration: item.duration || 0,
        mood: item.mood || 'neutral',
      }));
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Generate Video from Script
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Enter a script and let AI create a comprehensive video production plan.
      </Typography>

      {error && <ErrorAlert error={error} onClose={() => setError(null)} />}

      <Grid container spacing={4}>
        {/* Input Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Script Input
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={8}
              label="Video Script"
              placeholder="Enter your video script here... Describe scenes, characters, actions, and dialogue."
              value={script}
              onChange={(e) => setScript(e.target.value)}
              required
              sx={{ mb: 3 }}
            />

            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>AI Model</InputLabel>
              <Select
                value={model}
                label="AI Model"
                onChange={(e) => setModel(e.target.value)}
              >
                {models.map((modelOption) => (
                  <MenuItem key={modelOption.value} value={modelOption.value}>
                    {modelOption.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              variant="contained"
              size="large"
              fullWidth
              startIcon={<VideoLibrary />}
              onClick={handleGenerate}
              disabled={loading || !script.trim()}
            >
              {loading ? 'Generating...' : 'Generate Video Plan'}
            </Button>
          </Paper>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={6}>
          {loading && (
            <LoadingSpinner message="AI is analyzing your script and creating a video plan..." />
          )}

          {result && (
            <Box>
              {/* Summary Card */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Video Plan Summary
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip label={`${result.clips.clips.length} Clips`} color="primary" />
                    <Chip label={`${result.narrations.word_count} Words`} color="secondary" />
                    <Chip label={`${result.total_duration}s Duration`} color="success" />
                    <Chip label={`${result.bgms.bgm_options.length} BGM Options`} />
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      startIcon={<Download />}
                      onClick={handleDownload}
                      size="small"
                    >
                      Download Plan
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<PlayArrow />}
                      size="small"
                      disabled
                    >
                      Preview (Coming Soon)
                    </Button>
                  </Box>
                </CardContent>
              </Card>

              {/* Clips */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Generated Clips
                  </Typography>
                  <Grid container spacing={2}>
                    {result.clips.clips.map((clip) => (
                      <Grid item xs={12} sm={6} key={clip.id}>
                        <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Clip {clip.id}
                          </Typography>
                          <Typography variant="body2" sx={{ mb: 1 }}>
                            {clip.description}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Chip label={clip.mood} size="small" />
                            <Chip label={`${clip.duration}s`} size="small" variant="outlined" />
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>

              {/* Narration */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Narration Script
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2">
                      {result.narrations.narration}
                    </Typography>
                  </Paper>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Word count: {result.narrations.word_count}
                  </Typography>
                </CardContent>
              </Card>

              {/* BGM Options */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Background Music Options
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    {result.bgms.bgm_options.map((bgm, index) => (
                      <Chip key={index} label={bgm} variant="outlined" />
                    ))}
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" gutterBottom>
                    Mood Analysis
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {Object.entries(result.bgms.mood_analysis).map(([mood, count]) => (
                      <Chip key={mood} label={`${mood}: ${count}`} size="small" />
                    ))}
                  </Box>
                </CardContent>
              </Card>

              {/* Timeline Chart */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Timeline Visualization
                  </Typography>
                  <Box sx={{ height: 300, width: '100%' }}>
                    <ResponsiveContainer>
                      <BarChart data={formatTimelineData(result.timeline)}>
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
            </Box>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Generate;