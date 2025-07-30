export interface VideoResponse {
  clips: {
    clips: Array<{
      id: number;
      description: string;
      duration: number;
      mood: string;
      scene_id: number;
    }>;
  };
  narrations: {
    narration: string;
    word_count: number;
  };
  bgms: {
    bgm_options: string[];
    mood_analysis: Record<string, number>;
  };
  timeline: Array<{
    time: number;
    event: string;
    description: string;
    duration?: number;
    clip_id?: number;
    mood?: string;
  }>;
  total_duration: number;
  assembly_metadata: {
    clip_count: number;
    narration_word_count: number;
    bgm_options_count: number;
    created_at: string;
  };
}

export interface VideoProcessResponse {
  final_video: string;
  plan: string;
  source_video: string;
  processing_type: string;
  coverage_percentage: number;
  scene_count: number;
}

export interface UploadResponse {
  session_id: string;
  filename: string;
  ws_token?: string;
}

export interface SessionInfo {
  session_id: string;
  filename: string;
  edits_count: number;
  finalized: boolean;
  last_activity: number;
  file_size: number;
  video_duration?: number;
  preview_path?: string;
  video_path?: string;
}

export interface EditCommand {
  command: string;
  parameters: Record<string, any>;
}

export interface TrimRequest {
  start_time: string;
  end_time: string;
  preview_only?: boolean;
  quality?: string;
}

export interface ThumbnailRequest {
  time: string;
}

export interface AnalysisRequest {
  detailed?: boolean;
  preferences?: Record<string, any>;
}

export interface SuggestionsRequest {
  max_suggestions?: number;
}

export interface OptimizationRequest {
  target_platform?: string;
  quality_level?: string;
}

export interface ApiError {
  detail: string;
}