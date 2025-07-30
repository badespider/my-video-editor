import React, { useState } from 'react';
import { Container, Typography, Button, Box, Paper, Alert, LinearProgress } from '@mui/material';
import { CloudUpload } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';
import { useAppContext } from '../context/AppContext';

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const { setSessionId } = useAppContext();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setError(null);
    setSuccess(null);
    setUploadProgress(0);

    try {
      const response = await apiService.uploadVideo(file, (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      setSessionId(response.session_id);
      setSuccess(`Video uploaded successfully! Session ID: ${response.session_id}`);
      
      // Navigate to preview after a short delay
      setTimeout(() => {
        navigate('/preview');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload video');
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
    },
    maxFiles: 1,
    disabled: uploading
  });

  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Video
      </Typography>

      <Paper sx={{ p: 4, mt: 3 }}>
        <Box
          {...getRootProps()}
          sx={{
            border: 2,
            borderColor: isDragActive ? 'primary.main' : 'grey.300',
            borderStyle: 'dashed',
            borderRadius: 2,
            p: 6,
            textAlign: 'center',
            cursor: uploading ? 'not-allowed' : 'pointer',
            backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
            transition: 'all 0.2s ease-in-out',
          }}
        >
          <input {...getInputProps()} />
          <CloudUpload sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Drop the video here...' : 'Drag & drop a video file here'}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            or click to select a file
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Supported formats: MP4, MKV, AVI, MOV, WMV
          </Typography>
        </Box>

        {uploading && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" gutterBottom>
              Uploading... {uploadProgress}%
            </Typography>
            <LinearProgress variant="determinate" value={uploadProgress} />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {success}
          </Alert>
        )}
      </Paper>
    </Container>
  );
};

export default Upload;