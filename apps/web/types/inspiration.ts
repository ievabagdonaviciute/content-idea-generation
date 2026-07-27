export type NotionStatus = "New" | "Processing" | "Processed" | "Failed";
export type Availability = "full_media" | "transcript_only" | "metadata_only" | "unavailable" | null;

export interface InspirationItemOut {
  id: string;
  notion_page_id: string;
  title: string | null;
  tiktok_url: string;
  tiktok_video_id: string | null;
  creator_name: string | null;
  topics: string[] | null;
  format_hint: string | null;
  note_why_saved: string | null;
  note_favorite_part: string | null;
  notion_status: NotionStatus;
  availability: Availability;
  thumbnail_url: string | null;
  embed_html: string | null;
  processed_at: string | null;
  error_message: string | null;
  already_used: boolean;
  created_at: string;
}

export interface SyncRunOut {
  id: string;
  source: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  items_processed: number;
  items_failed: number;
  error_summary: string | null;
}
