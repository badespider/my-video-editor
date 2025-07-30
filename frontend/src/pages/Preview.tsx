import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Paper,
  Grid,
  Card,
  CardContent,
  Alert,
} from '@mui/material';
import { PlayArrow, Download, Refresh, Image } from '@mui/icons-material';
import ReactPlayer from 'react-player';
import { useAppContext } from '../context/AppContext';
import ApiService from '../services/api';
import ErrorAlert from '../components/Common/ErrorAlert';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { SessionInfo } from '../types/api';

const Preview: React.FC = () => {
  const { state } = useAppContext();
  const [sessionId, setSessionId] = useState(state.currentSessionId || '');
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [thumbnailTime, setThumbnailTime] = useState('00:00:30');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [playerReady, setPlayerReady] = useState(false);

  useEffect(() => {
    if (sessionId) {
      loadPreview();
    }
  }, [sessionId]);

  const loadPreview = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load session info
      const info = await ApiService.getSessionInfo(sessionId);
      setSessionInfo(info);
      
      // Set preview URL
      const url = ApiService.getPreviewUrl(sessionId);
      setPreviewUrl(url);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load preview');
      console.error('Preview error:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateThumbnail = async () => {
    if (!sessionId) return;

    try {
      setLoading(true);
      const response = await ApiService.generateThumbnail(sessionId, {
        time: thumbnailTime,
      });
      
      setThumbnailUrl(ApiService.getFileUrl(response.thumbnail_path));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate thumbnail');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (previewUrl) {
      const link = document.createElement('a');
      link.href = previewUrl;
      link.download = `preview_${sessionId}.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Video Preview
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Preview your video with real-time updates and generate thumbnails.
      </Typography>

      {error && <ErrorAlert error={error} onClose={() => setError(null)} />}

      <Grid container spacing={4}>
        {/* Session Input */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <TextField
                label="Session ID"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                placeholder="Enter session ID"
                sx={{ flexGrow: 1 }}
              />
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={loadPreview}
                disabled={!sessionId || loading}
              >
                Load Preview
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Video Player */}
        <Grid item xs={12} md={8}>
          {loading && <LoadingSpinner message="Loading preview..." />}
          
          {previewUrl && !loading && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Video Preview
                </Typography>
                
                <Box sx={{ position: 'relative', paddingTop: '56.25%', mb: 2 }}>
                  <ReactPlayer
                    url={previewUrl}
                    width="100%"
                    height="100%"
                    style={{ position: 'absolute', top: 0, left: 0 }}
                    controls
                    onReady={() => setPlayerReady(true)}
                    onError={(error) => {
                      console.error('Player error:', error);
                      setError('Failed to load video player');
                    }}
                    config={{
                      file: {
                        attributes: {
                          crossOrigin: 'anonymous',
                        },
                      },
                    }}
                  />
                </Box>

                {!playerReady && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Loading video player...
                  </Alert>
                )}

                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    onClick={handleDownload}
                    disabled={!playerReady}
                  >
                    Download Preview
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    onClick={loadPreview}
                  >
                    Refresh
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}

          {!previewUrl && !loading && sessionId && (
            <Alert severity="warning">
              No preview available for this session. Make sure the session ID is correct and the video has been processed.
            </Alert>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Session Info */}
          {sessionInfo && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Session Information
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>File:</strong> {sessionInfo.filename}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>File Size:</strong> {(sessionInfo.file_size / (1024 * 1024)).toFixed(2)} MB
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Edits Applied:</strong> {sessionInfo.edits_count}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>Status:</strong> {sessionInfo.finalized ? 'Finalized' : 'Active'}
                </Typography>
                {sessionInfo.video_duration && (
                  <Typography variant="body2">
                    <strong>Duration:</strong> {Math.round(sessionInfo.video_duration)}s
                  </Typography>
                )}
              </CardContent>
            </Card>
          )}

          {/* Thumbnail Generator */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Generate Thumbnail
              </Typography>
              
              <TextField
                fullWidth
                label="Time Position"
                value={thumbnailTime}
                onChange={(e) => setThumbnailTime(e.target.value)}
                placeholder="00:00:30"
                helperText="Format: HH:MM:SS"
                sx={{ mb: 2 }}
              />

              <Button
                variant="outlined"
                startIcon={<Image />}
                onClick={generateThumbnail}
                disabled={!sessionId || loading}
                fullWidth
                sx={{ mb: 2 }}
              >
                Generate Thumbnail
              </Button>

              {thumbnailUrl && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Generated Thumbnail
                  </Typography>
                  <img
                    src={thumbnailUrl}
                    alt="Video thumbnail"
                    style={{
                      width: '100%',
                      height: 'auto',
                      borderRadius: 4,
                      border: '1px solid #ddd',
                    }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Preview;