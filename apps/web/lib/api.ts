import { API_BASE_URL } from "./config";
import type { Page } from "@/types/common";
import type { OwnPostOut } from "@/types/posts";
import type { InspirationItemOut, SyncRunOut } from "@/types/inspiration";
import type { ContentProfileSnapshotOut } from "@/types/profile";
import type {
  ContentIdeaOut,
  GeneratedBriefOut,
  GeneratedScriptOut,
  IdeaFeedbackRequest,
  IdeaGenerateRequest,
  IdeaSourcedMediaOut,
  ScriptGenerateRequest,
} from "@/types/ideas";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? detail;
    } catch {
      // response body wasn't JSON -- fall back to statusText
    }
    throw new ApiError(response.status, typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

function query(params: Record<string, number | string | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined);
  if (entries.length === 0) return "";
  const search = new URLSearchParams(entries.map(([k, v]) => [k, String(v)]));
  return `?${search.toString()}`;
}

export const api = {
  health: () => request<{ status: string; project_name: string; app_env: string }>("/health"),

  // Own posts
  listPosts: (limit = 50, offset = 0) =>
    request<Page<OwnPostOut>>(`/posts${query({ limit, offset })}`),
  getPost: (id: string) => request<OwnPostOut>(`/posts/${id}`),
  reanalyzePost: (id: string) => request<OwnPostOut>(`/posts/${id}/reanalyze`, { method: "POST" }),

  // Sync
  syncTikTok: () => request<SyncRunOut>("/sync/tiktok", { method: "POST" }),
  listSyncRuns: (limit = 20, offset = 0) =>
    request<Page<SyncRunOut>>(`/sync-runs${query({ limit, offset })}`),

  // Inspiration
  listInspiration: (limit = 50, offset = 0) =>
    request<Page<InspirationItemOut>>(`/inspiration${query({ limit, offset })}`),
  getInspirationItem: (id: string) => request<InspirationItemOut>(`/inspiration/${id}`),
  reanalyzeInspirationItem: (id: string) =>
    request<InspirationItemOut>(`/inspiration/${id}/reanalyze`, { method: "POST" }),
  syncNotion: () => request<SyncRunOut>("/inspiration/sync-notion", { method: "POST" }),
  markInspirationUsed: (id: string) =>
    request<InspirationItemOut>(`/inspiration/${id}/mark-used`, { method: "POST" }),
  unmarkInspirationUsed: (id: string) =>
    request<InspirationItemOut>(`/inspiration/${id}/unmark-used`, { method: "POST" }),

  // Profile
  getProfile: () => request<ContentProfileSnapshotOut>("/profile"),
  rebuildProfile: () => request<ContentProfileSnapshotOut>("/profile/rebuild", { method: "POST" }),

  // Ideas
  listIdeas: (limit = 50, offset = 0, status?: string) =>
    request<Page<ContentIdeaOut>>(`/ideas${query({ limit, offset, status })}`),
  getIdea: (id: string) => request<ContentIdeaOut>(`/ideas/${id}`),
  generateIdeas: (body: IdeaGenerateRequest) =>
    request<ContentIdeaOut[]>("/ideas/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  submitIdeaFeedback: (id: string, body: IdeaFeedbackRequest) =>
    request<ContentIdeaOut>(`/ideas/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  generateBrief: (id: string) =>
    request<GeneratedBriefOut>(`/ideas/${id}/brief`, { method: "POST" }),
  getBrief: (id: string) => request<GeneratedBriefOut>(`/ideas/${id}/brief`),
  generateScript: (id: string, body: ScriptGenerateRequest) =>
    request<GeneratedScriptOut>(`/ideas/${id}/script`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  getScript: (id: string) => request<GeneratedScriptOut>(`/ideas/${id}/script`),
  generateIdeaMedia: (id: string) =>
    request<IdeaSourcedMediaOut>(`/ideas/${id}/media`, { method: "POST" }),
  getIdeaMedia: (id: string) => request<IdeaSourcedMediaOut>(`/ideas/${id}/media`),
  setIdeaStatus: (id: string, status: string) =>
    request<ContentIdeaOut>(`/ideas/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    }),
};
