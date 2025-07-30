import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Paper,
  Alert,
  Chip,
} from '@mui/material';
import { CloudUpload, CheckCircle } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import ApiService from '../services/api';
import ProgressBar from '../components/Common/ProgressBar';
import ErrorAlert from '../components/Common/ErrorAlert';
import { useAppContext } from '../context/AppContext';

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const { dispatch } = useAppContext();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const maxFileSize = 100 * 1024 * 1024; // 100MB
  const allowedTypes = ['video/mp4', 'video/mkv', 'video/avi', 'video/mov'];

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'video/*': ['.mp4', '.mkv', '.avi', '.mov'],
    },
    maxSize: maxFileSize,
    multiple: false,
    onDrop: (acceptedFiles, rejectedFiles) => {
      if (rejectedFiles.length > 0) {
        const rejection = rejectedFiles[0];
        if (rejection.errors.some(e => e.code === 'file-too-large')) {
          setError(`File is too large. Maximum size is ${maxFileSize / (1024 * 1024)}MB`);
        } else if (rejection.errors.some(e => e.code === 'file-invalid-type')) {
          setError('Invalid file type. Please upload MP4, MKV, AVI, or MOV files.');
        } else {
          setError('File rejected. Please check the file and try again.');
        }
        return;
      }

      if (acceptedFiles.length > 0) {
        setSelectedFile(acceptedFiles[0]);
        setError(null);
      }
    },
  });

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file to upload');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setUploadProgress(0);

      const response = await ApiService.uploadVideo(selectedFile, (progress) => {
        setUploadProgress(progress);
      });

      dispatch({ type: 'SET_SESSION_ID', payload: response.session_id });
      setSuccess(`Upload successful! Session ID: ${response.session_id}`);
      
      // Navigate to preview after 2 seconds
      setTimeout(() => {
        navigate('/preview');
      }, 2000);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
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
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Upload Video
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Upload your video file to start the AI-powered editing process.
      </Typography>

      {error && <ErrorAlert error={error} onClose={() => setError(null)} />}
      
      {success && (
        <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

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
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop the video file here' : 'Drag & drop a video file here'}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          or click to select a file
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, flexWrap: 'wrap' }}>
          <Chip label="MP4" size="small" />
          <Chip label="MKV" size="small" />
          <Chip label="AVI" size="small" />
          <Chip label="MOV" size="small" />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Maximum file size: {maxFileSize / (1024 * 1024)}MB
        </Typography>
      </Paper>

      {/* Selected File Info */}
      {selectedFile && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Selected File
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Typography variant="body1">
              <strong>Name:</strong> {selectedFile.name}
            </Typography>
            <Chip label={formatFileSize(selectedFile.size)} size="small" />
          </Box>
          <Typography variant="body2" color="text.secondary">
            <strong>Type:</strong> {selectedFile.type}
          </Typography>
        </Paper>
      )}

      {/* Description Field */}
      <TextField
        fullWidth
        multiline
        rows={3}
        label="Description (Optional)"
        placeholder="Describe your video content..."
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        sx={{ mb: 3 }}
      />

      {/* Upload Progress */}
      {uploading && (
        <ProgressBar
          progress={uploadProgress}
          label="Uploading video..."
          showPercentage
        />
      )}

      {/* Upload Button */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<CloudUpload />}
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          sx={{ minWidth: 200 }}
        >
          {uploading ? 'Uploading...' : 'Upload Video'}
        </Button>
        
        {selectedFile && !uploading && (
          <Button
            variant="outlined"
            size="large"
            onClick={() => {
              setSelectedFile(null);
              setDescription('');
              setError(null);
              setSuccess(null);
            }}
          >
            Clear
          </Button>
        )}
      </Box>

      {/* Upload Tips */}
      <Paper sx={{ p: 3, mt: 4, bgcolor: 'info.light', color: 'info.contrastText' }}>
        <Typography variant="h6" gutterBottom>
          Upload Tips
        </Typography>
        <ul style={{ margin: 0, paddingLeft: 20 }}>
          <li>Supported formats: MP4, MKV, AVI, MOV</li>
          <li>Maximum file size: {maxFileSize / (1024 * 1024)}MB</li>
          <li>Higher quality videos provide better AI analysis results</li>
          <li>Processing time depends on video length and complexity</li>
        </ul>
      </Paper>
    </Container>
  );
};

export default Upload;