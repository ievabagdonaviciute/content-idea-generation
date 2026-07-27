export interface SourceVideoOut {
  external_video_id: string;
  permalink: string;
  caption: string | null;
  posted_at: string | null;
  duration_seconds: number | null;
  stats: Record<string, unknown> | null;
}

export interface ContentAnalysisOut {
  primary_topic: string;
  secondary_topics: string[];
  content_format: string;
  presentation_style: string[];
  hook_text: string;
  hook_type: string;
  hook_mechanism: string;
  tone: string[];
  story_structure: string[];
  audience_promise: string;
  emotional_angle: string | null;
  cta_pattern: string | null;
  editing_intensity: "low" | "medium" | "high";
  estimated_pacing: "slow" | "medium" | "fast";
  personal_story_level: number;
  educational_level: number;
  visual_analysis_available: boolean;
  transcript_available: boolean;
  confidence: number;
}

export type ProcessingStatus = "pending" | "processing" | "completed" | "failed";

export interface OwnPostOut {
  id: string;
  processing_status: ProcessingStatus;
  processing_error: string | null;
  source_video: SourceVideoOut;
  content_analysis: ContentAnalysisOut | null;
  created_at: string;
}
