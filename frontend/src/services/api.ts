import axios, { AxiosProgressEvent } from 'axios';

// Dynamic API base URL that works in different environments
const getApiBaseUrl = () => {
  if (process.env.REACT_APP_API_BASE_URL) {
    return process.env.REACT_APP_API_BASE_URL;
  }
  
  // In webcontainer or proxied environments, use relative URLs
  if (window.location.hostname.includes('webcontainer') || 
      window.location.hostname.includes('local-credentialless')) {
    return '/api';  // Use relative path for proxy
  }
  
  // Default for local development
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for long operations
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for logging and error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Root endpoint
  getRoot: () => api.get('/').then(res => res.data),

  // Upload video
  uploadVideo: (file: File, onUploadProgress?: (progressEvent: AxiosProgressEvent) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload/video', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress,
    }).then(res => res.data);
  },

  // Generate video from script
  generateVideo: (data: { script: string; model?: string }) =>
    api.post('/generate', data).then(res => res.data),

  // Process video
  processVideo: (data: { video_path?: string; model?: string }) =>
    api.post('/process_video', data).then(res => res.data),

  // Apply edits
  applyEdits: (sessionId: string, data: { edits: Array<{ command: string; parameters: any }> }) =>
    api.post(`/apply_edits/${sessionId}`, data).then(res => res.data),

  // Trim video
  trimVideo: (sessionId: string, data: { start_time: number; end_time: number; preview_only?: boolean; quality?: string }) =>
    api.post(`/trim/${sessionId}`, data).then(res => res.data),

  // Preview video
  getPreview: (sessionId: string, range?: string) => {
    const headers = range ? { Range: range } : {};
    return api.get(`/preview/${sessionId}`, { headers, responseType: 'blob' });
  },

  // Finalize video
  finalizeVideo: (sessionId: string) =>
    api.post(`/finalize/${sessionId}`).then(res => res.data),

  // Get session info
  getSessionInfo: (sessionId: string) =>
    api.get(`/session/${sessionId}`).then(res => res.data),

  // Generate thumbnail
  generateThumbnail: (sessionId: string, data: { time: string }) =>
    api.post(`/thumbnail/${sessionId}`, data).then(res => res.data),

  // Analyze video
  analyzeVideo: (sessionId: string, data: { detailed?: boolean; preferences?: any }) =>
    api.post(`/analyze/${sessionId}`, data).then(res => res.data),

  // Get suggestions
  getSuggestions: (sessionId: string, data: { max_suggestions?: number }) =>
    api.post(`/suggestions/${sessionId}`, data).then(res => res.data),

  // Optimize video
  optimizeVideo: (sessionId: string, data: { target_platform?: string; quality_level?: string }) =>
    api.post(`/optimization/${sessionId}`, data).then(res => res.data),

  // Get file
  getFile: (filename: string) => `${API_BASE_URL}/file/${filename}`,
};