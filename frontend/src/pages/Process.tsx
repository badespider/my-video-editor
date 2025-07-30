import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
} from '@mui/material';
import { Settings, PlayArrow, Download } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import ReactPlayer from 'react-player';
import ApiService from '../services/api';
import ProgressBar from '../components/Common/ProgressBar';
import ErrorAlert from '../components/Common/ErrorAlert';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { VideoProcessResponse } from '../types/api';
import { useAppContext } from '../context/AppContext';

const Process: React.FC = () => {
  const { state, dispatch } = useAppContext();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [model, setModel] = useState('');
  const [processing, setProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VideoProcessResponse | null>(null);

  const models = [
    { value: '', label: 'Default' },
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'grok-4', label: 'Grok-4' },
    { value: 'mock', label: 'Mock (Testing)' },
  ];

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'video/*': ['.mp4', '.mkv', '.avi', '.mov'],
    },
    maxSize: 100 * 1024 * 1024, // 100MB
    multiple: false,
    onDrop: (acceptedFiles, rejectedFiles) => {
      if (rejectedFiles.length > 0) {
        setError('Invalid file. Please upload a video file under 100MB.');
        return;
      }

      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
        setError(null);
      }
    },
  });

  const handleProcess = async () => {
    if (!selectedFile) {
      setError('Please select a video file to process');
      return;
    }

    try {
      setProcessing(true);
      setError(null);
      setUploadProgress(0);

      const response = await ApiService.processVideo(
        selectedFile,
        undefined,
        model || undefined,
        (progress) => {
          setUploadProgress(progress);
        }
      );

      setResult(response);
      
      // Extract session ID from the response if available
      if (response.source_video) {
        // This is a simplified approach - in a real app, you'd get the session ID from the upload
        const sessionId = `session_${Date.now()}`;
        dispatch({ type: 'SET_SESSION_ID', payload: sessionId });
      }

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Processing failed. Please try again.');
      console.error('Process error:', err);
    } finally {
      setProcessing(false);
    }
  };

  const handleDownload = () => {
    if (result?.final_video) {
      const link = document.createElement('a');
      link.href = ApiService.getFileUrl(result.final_video);
      link.download = result.final_video;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Process Video
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Upload and process videos with AI-powered analysis and editing.
      </Typography>

      {error && <ErrorAlert error={error} onClose={() => setError(null)} />}

      <Grid container spacing={4}>
        {/* Upload Section */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Upload Video for Processing
            </Typography>

            {/* File Drop Zone */}
            <Paper
              {...getRootProps()}
              sx={{
                p: 4,
                mb: 3,
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                bgcolor: isDragActive ? 'action.hover' : 'background.paper',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.2s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: 'action.hover',
                },
              }}
            >
              <input {...getInputProps()} />
              <Settings sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive ? 'Drop the video file here' : 'Drag & drop a video file here'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                or click to select a file
              </Typography>
            </Paper>

            {/* Selected File Info */}
            {selectedFile && (
              <Alert severity="info" sx={{ mb: 3 }}>
                <Typography variant="body2">
                  <strong>Selected:</strong> {selectedFile.name} ({formatFileSize(selectedFile.size)})
                </Typography>
              </Alert>
            )}

            {/* Model Selection */}
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

            {/* Upload Progress */}
            {processing && (
              <ProgressBar
                progress={uploadProgress}
                label="Processing video..."
                showPercentage
              />
            )}

            {/* Process Button */}
            <Button
              variant="contained"
              size="large"
              fullWidth
              startIcon={<Settings />}
              onClick={handleProcess}
              disabled={!selectedFile || processing}
            >
              {processing ? 'Processing...' : 'Process Video'}
            </Button>
          </Paper>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} md={6}>
          {processing && !result && (
            <LoadingSpinner message="AI is analyzing your video..." />
          )}

          {result && (
            <Box>
              {/* Summary Card */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Processing Results
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip label={`${result.scene_count} Scenes`} color="primary" />
                    <Chip 
                      label={`${(result.coverage_percentage * 100).toFixed(1)}% Coverage`} 
                      color="secondary" 
                    />
                    <Chip label={result.processing_type} />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    <strong>Source:</strong> {result.source_video}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      variant="contained"
                      startIcon={<Download />}
                      onClick={handleDownload}
                      size="small"
                    >
                      Download Result
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<PlayArrow />}
                      size="small"
                      disabled
                    >
                      Preview
                    </Button>
                  </Box>
                </CardContent>
              </Card>

              {/* Plan Details */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Processing Plan
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                      {typeof result.plan === 'string' ? result.plan : JSON.stringify(result.plan, null, 2)}
                    </Typography>
                  </Paper>
                </CardContent>
              </Card>

              {/* Video Player (if final video is available) */}
              {result.final_video && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Processed Video
                    </Typography>
                    <Box sx={{ position: 'relative', paddingTop: '56.25%' }}>
                      <ReactPlayer
                        url={ApiService.getFileUrl(result.final_video)}
                        width="100%"
                        height="100%"
                        style={{ position: 'absolute', top: 0, left: 0 }}
                        controls
                        onError={(error) => {
                          console.error('Player error:', error);
                        }}
                      />
                    </Box>
                  </CardContent>
                </Card>
              )}
            </Box>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default Process;