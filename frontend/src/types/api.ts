// API Response Types
export interface VideoClip {
  id?: string;
  description?: string;
  prompt?: string;
  duration?: number;
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
  id?: string;
  name?: string;
  file_path?: string;
  duration?: number;
}

export interface TimelineItem {
  type: 'clip' | 'narration' | 'bgm';
  start_time: number;
  end_time: number;
  content: VideoClip | Narration | BGM;
}

export interface VideoResponse {
  clips: VideoClip[];
  narrations: Narration[];
  bgms: BGM[];
  timeline: TimelineItem[];
  total_duration: number;
  assembly_metadata?: any;
  final_video?: string;
  session_id?: string;
}

export interface VideoProcessResponse {
  final_video: string;
  plan: any;
  coverage_percentage: number;
  scene_count: number;
  session_id?: string;
}

export interface UploadResponse {
  session_id: string;
  file_path: string;
  message: string;
}

export interface SessionInfo {
  session_id: string;
  video_path?: string;
  edits: any[];
  preview_path?: string;
  created_at: string;
  updated_at: string;
}

export interface AnalysisResponse {
  scenes?: any[];
  emotional_arc?: any;
  insights?: string[] | string;
  recommendations?: string[];
}

export interface SuggestionsResponse {
  suggestions: Array<{
    title?: string;
    description: string;
    confidence?: number;
    type?: string;
  }>;
}

export interface OptimizationResponse {
  optimized_path: string;
  settings: any;
  improvements: string[];
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