import axios, { AxiosProgressEvent } from 'axios';
import {
  VideoResponse,
  VideoProcessResponse,
  UploadResponse,
  SessionInfo,
  EditCommand,
  TrimRequest,
  ThumbnailRequest,
  AnalysisRequest,
  SuggestionsRequest,
  OptimizationRequest,
  ApiError
} from '../types/api';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes for long operations
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export class ApiService {
  // Root endpoint
  static async getRoot(): Promise<{ message: string }> {
    const response = await api.get('/');
    return response.data;
  }

  // Health check
  static async getHealth(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  }

  // Upload video
  static async uploadVideo(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload/video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  }

  // Generate video from script
  static async generateVideo(script: string, model?: string): Promise<VideoResponse> {
    const response = await api.post('/generate', {
      script,
      model,
    });
    return response.data;
  }

  // Process uploaded video
  static async processVideo(
    file?: File,
    videoPath?: string,
    model?: string,
    onProgress?: (progress: number) => void
  ): Promise<VideoProcessResponse> {
    if (file) {
      const formData = new FormData();
      formData.append('video', file);
      if (model) formData.append('model', model);

      const response = await api.post('/process_video', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (progressEvent.total && onProgress) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      });

      return response.data;
    } else {
      const response = await api.post('/process_video', {
        video_path: videoPath,
        model,
      });
      return response.data;
    }
  }

  // Session management
  static async getSessionInfo(sessionId: string): Promise<SessionInfo> {
    const response = await api.get(`/session/${sessionId}`);
    return response.data;
  }

  // Video editing
  static async applyEdits(sessionId: string, edits: EditCommand[]): Promise<any> {
    const response = await api.post(`/apply_edits/${sessionId}`, { edits });
    return response.data;
  }

  static async trimVideo(sessionId: string, trimRequest: TrimRequest): Promise<any> {
    const response = await api.post(`/trim/${sessionId}`, trimRequest);
    return response.data;
  }

  // Preview and finalization
  static getPreviewUrl(sessionId: string): string {
    return `${API_BASE_URL}/preview/${sessionId}`;
  }

  static getFileUrl(filename: string): string {
    return `${API_BASE_URL}/file/${filename}`;
  }

  static async finalizeVideo(sessionId: string): Promise<{ final_video_path: string }> {
    const response = await api.post(`/finalize/${sessionId}`);
    return response.data;
  }

  // Thumbnail generation
  static async generateThumbnail(
    sessionId: string,
    thumbnailRequest: ThumbnailRequest
  ): Promise<{ thumbnail_path: string; thumbnail_url: string }> {
    const response = await api.post(`/thumbnail/${sessionId}`, thumbnailRequest);
    return response.data;
  }

  // AI Analysis
  static async analyzeVideo(
    sessionId: string,
    analysisRequest: AnalysisRequest = {}
  ): Promise<any> {
    const response = await api.post(`/analyze/${sessionId}`, analysisRequest);
    return response.data;
  }

  // AI Suggestions
  static async getSuggestions(
    sessionId: string,
    suggestionsRequest: SuggestionsRequest = {}
  ): Promise<any> {
    const response = await api.post(`/suggestions/${sessionId}`, suggestionsRequest);
    return response.data;
  }

  // Optimization
  static async optimizeVideo(
    sessionId: string,
    optimizationRequest: OptimizationRequest = {}
  ): Promise<any> {
    const response = await api.post(`/optimize/${sessionId}`, optimizationRequest);
    return response.data;
  }
}

export default ApiService;