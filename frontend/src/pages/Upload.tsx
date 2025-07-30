import React, { useState } from 'react';
import { Container, Typography, Box, Button, Paper, LinearProgress, Alert } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppContext } from '../context/AppContext';
import { apiService } from '../services/api';

const Upload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const { setSessionId } = useAppContext();
  const navigate = useNavigate();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);
    setError(null);

    try {
      const response = await apiService.uploadVideo(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 1));
        setProgress(percentCompleted);
      });

      setSessionId(response.session_id);
      navigate('/preview');
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Video
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        <Box
          sx={{
            border: '2px dashed #ccc',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            '&:hover': {
              borderColor: 'primary.main',
              backgroundColor: 'action.hover',
            },
          }}
          onClick={() => document.getElementById('file-input')?.click()}
        >
          <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {file ? file.name : 'Click to select a video file'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Supported formats: MP4, MKV, AVI, MOV
          </Typography>
          <input
            id="file-input"
            type="file"
            accept=".mp4,.mkv,.avi,.mov"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </Box>

        {file && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" color="text.secondary">
              File size: {(file.size / (1024 * 1024)).toFixed(2)} MB
            </Typography>
          </Box>
        )}

        {uploading && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" gutterBottom>
              Uploading... {progress}%
            </Typography>
            <LinearProgress variant="determinate" value={progress} />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 3, textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleUpload}
            disabled={!file || uploading}
          >
            {uploading ? 'Uploading...' : 'Upload Video'}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default Upload;