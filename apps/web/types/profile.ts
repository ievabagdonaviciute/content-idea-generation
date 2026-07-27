export interface ContentProfileSnapshotOut {
  id: string;
  sample_size: number;
  content_pillars: Record<string, unknown>[];
  format_distribution: Record<string, unknown>[];
  underused_formats: string[];
  typical_hooks: Record<string, unknown>[];
  typical_structures: Record<string, unknown>[];
  tone_distribution: Record<string, unknown>[];
  polished_vs_casual_ratio: number | null;
  personal_story_frequency: number | null;
  recently_overused_topics: string[];
  recently_uncovered_topics: string[];
  frequent_combinations: Record<string, unknown>[];
  content_gaps: string[];
  observations_lt: string[];
  confidence_notes: string[];
  overall_confidence: number;
  created_at: string;
}
