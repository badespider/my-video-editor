// API Response Types
export interface RootResponse {
  message: string;
  status: string;
}

export interface UploadResponse {
  session_id: string;
  file_path: string;
  message: string;
}

export interface VideoClip {
  id?: string;
  description: string;
  duration: number;
  file_path?: string;
  start_time?: number;
  end_time?: number;
}

export interface Narration {
  text: string;
  timestamp?: number;
  duration?: number;
}

export interface BGM {
  name: string;
  file_path: string;
  duration: number;
}

export interface TimelineItem {
  type: 'clip' | 'narration' | 'bgm';
  start_time: number;
  end_time: number;
  content: VideoClip | Narration | BGM;
}

export interface VideoResponse {
  session_id?: string;
  clips: VideoClip[];
  narrations: Narration[];
  bgms: BGM[];
  timeline: TimelineItem[];
  total_duration: number;
  assembly_metadata?: any;
  final_video?: string;
}

export interface VideoProcessResponse {
  session_id: string;
  final_video: string;
  plan: any;
  coverage_percentage: number;
  scene_count: number;
  processing_time: number;
}

export interface EditCommand {
  command: string;
  parameters: any;
}

export interface ApplyEditsRequest {
  edits: EditCommand[];
}

export interface TrimRequest {
  start_time: number;
  end_time: number;
  preview_only?: boolean;
  quality?: string;
}

export interface ThumbnailRequest {
  time: string;
}

export interface ThumbnailResponse {
  thumbnail_path: string;
  timestamp: string;
}

export interface SessionInfo {
  session_id: string;
  video_path?: string;
  edits: EditCommand[];
  preview_path?: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisRequest {
  detailed?: boolean;
  preferences?: any;
}

export interface Scene {
  id: string;
  description: string;
  timestamp: string;
  duration: number;
  emotional_tone?: string;
}

export interface AnalysisResponse {
  session_id: string;
  scenes: Scene[];
  emotional_arc: any;
  insights: string;
  recommendations: string[];
  analysis_metadata: any;
}

export interface SuggestionsRequest {
  max_suggestions?: number;
}

export interface Suggestion {
  title: string;
  description: string;
  confidence: number;
  category: string;
}

export interface SuggestionsResponse {
  session_id: string;
  suggestions: Suggestion[];
  generated_at: string;
}

export interface OptimizationRequest {
  target_platform?: string;
  quality_level?: string;
}

export interface OptimizationResponse {
  session_id: string;
  optimized_video_path: string;
  optimization_report: any;
  performance_metrics: any;
}

// WebSocket Message Types
export interface WebSocketMessage {
  type: 'command' | 'response' | 'error' | 'status';
  data: any;
  timestamp: string;
}

export interface EditWebSocketMessage {
  command: string;
  parameters: any;
}