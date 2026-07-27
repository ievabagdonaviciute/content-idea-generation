export type NoveltyLevel = "aligned" | "stretch" | "experimental";
export type SimilarityCategory = "new" | "related_but_distinct" | "follow_up" | "too_similar";
export type IdeaStatus = "proposed" | "saved" | "archived";
export type ProductionEffort = "low" | "medium" | "high";
export type FeedbackRating = "love" | "maybe" | "not_for_me" | "already_covered";

export const FEEDBACK_RATINGS: { value: FeedbackRating; label: string }[] = [
  { value: "love", label: "Love it" },
  { value: "maybe", label: "Maybe" },
  { value: "not_for_me", label: "Not for me" },
  { value: "already_covered", label: "Already covered" },
];

export const SCRIPT_MODES: { value: string; label: string }[] = [
  { value: "polished_explainer", label: "Polished explainer" },
  { value: "casual_talking_head", label: "Casual talking head" },
  { value: "grwm_story", label: "GRWM story" },
  { value: "news_recap", label: "News recap" },
  { value: "comment_response", label: "Comment response" },
  { value: "personal_story", label: "Personal story" },
];

export interface ContentIdeaOut {
  id: string;
  title: string;
  concept: string;
  content_pillar: string;
  recommended_format: string;
  format_label_lt: string;
  why_it_fits_me: string;
  inspiration_pattern: string | null;
  originality_note: string | null;
  closest_existing_post_id: string | null;
  similarity_score: number;
  similarity_category: SimilarityCategory;
  novelty_level: NoveltyLevel;
  hook_options: string[];
  outline: string[];
  suggested_duration_seconds: number;
  production_effort: ProductionEffort;
  output_language: string;
  status: IdeaStatus;
  created_at: string;
}

export interface GeneratedBriefOut {
  id: string;
  idea_id: string;
  objective: string;
  target_viewer: string;
  promise: string;
  recommended_format: string;
  recommended_duration_seconds: number;
  hook_choices: string[];
  beats: { label: string; description: string }[];
  b_roll_suggestions: string[];
  on_screen_text: string[];
  editing_notes: string[];
  closing_line: string;
  call_to_action: string;
  caption_options: string[];
  hashtags: string[];
  claims_to_verify: string[];
  output_language: string;
}

export interface GeneratedScriptOut {
  id: string;
  idea_id: string;
  mode: string;
  spoken_lines: string[];
  editing_notes: string[];
  estimated_duration_seconds: number;
  placeholders: string[];
  output_language: string;
}

export interface IdeaGenerateRequest {
  count?: number;
  content_pillar?: string | null;
  recommended_format?: string | null;
  instructions?: string | null;
  excluded_subjects?: string[];
  output_language?: string | null;
}

export interface IdeaFeedbackRequest {
  rating: FeedbackRating;
  comment?: string | null;
}

export interface ScriptGenerateRequest {
  mode: string;
}
