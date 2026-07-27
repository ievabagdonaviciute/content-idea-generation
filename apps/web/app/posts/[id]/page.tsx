"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { strings } from "@/lib/strings";
import { Card } from "@/components/Card";
import { Badge, processingStatusTone } from "@/components/Badge";
import { ErrorView, LoadingView } from "@/components/StateViews";

export default function PostDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const postQuery = useQuery({
    queryKey: ["posts", params.id],
    queryFn: () => api.getPost(params.id),
  });

  const reanalyze = useMutation({
    mutationFn: () => api.reanalyzePost(params.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
  });

  if (postQuery.isError) {
    return <ErrorView error={postQuery.error} onRetry={() => postQuery.refetch()} />;
  }
  if (!postQuery.data) {
    return <LoadingView />;
  }

  const post = postQuery.data;
  const video = post.source_video;
  const analysis = post.content_analysis;
  const alreadyAnalyzed = post.processing_status === "completed";

  return (
    <div className="space-y-6">
      <Link href="/posts" className="text-sm text-brand-300 hover:underline">
        ← {strings.common.back}
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{strings.posts.detailTitle}</h1>
          <a
            href={video.permalink}
            target="_blank"
            rel="noreferrer"
            className="mt-1 block text-sm text-brand-300 hover:underline"
          >
            {video.permalink}
          </a>
        </div>
        <Badge tone={processingStatusTone(post.processing_status)}>
          {strings.posts.status[post.processing_status]}
        </Badge>
      </div>

      <Card>
        <p className="text-slate-200">{video.caption || "—"}</p>
        <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-slate-500">Posted</dt>
            <dd className="text-slate-300">
              {video.posted_at ? new Date(video.posted_at).toLocaleDateString() : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Duration</dt>
            <dd className="text-slate-300">{video.duration_seconds ?? "—"}s</dd>
          </div>
          <div>
            <dt className="text-slate-500">External ID</dt>
            <dd className="truncate text-slate-300">{video.external_video_id}</dd>
          </div>
        </dl>
      </Card>

      <div>
        <button
          onClick={() => reanalyze.mutate()}
          disabled={reanalyze.isPending}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >
          {reanalyze.isPending
            ? strings.posts.reanalyzing
            : alreadyAnalyzed
              ? strings.posts.reanalyzeAgain
              : strings.posts.reanalyze}
        </button>
        {reanalyze.isError ? <ErrorView error={reanalyze.error} /> : null}
      </div>

      {post.processing_error ? (
        <ErrorView error={new Error(post.processing_error)} />
      ) : null}

      <div>
        <h2 className="mb-3 text-lg font-medium text-slate-200">{strings.posts.analysis}</h2>
        {analysis ? (
          <Card className="space-y-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Primary topic</p>
              <p className="text-slate-100">{analysis.primary_topic}</p>
            </div>
            {analysis.secondary_topics.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {analysis.secondary_topics.map((topic) => (
                  <Badge key={topic}>{topic}</Badge>
                ))}
              </div>
            ) : null}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Format</p>
                <p className="text-slate-200">{analysis.content_format}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Pacing / editing</p>
                <p className="text-slate-200">
                  {analysis.estimated_pacing} / {analysis.editing_intensity}
                </p>
              </div>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Hook</p>
              <p className="text-slate-200">&ldquo;{analysis.hook_text}&rdquo;</p>
              <p className="text-sm text-slate-400">
                {analysis.hook_type} — {analysis.hook_mechanism}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-500">Audience promise</p>
              <p className="text-slate-200">{analysis.audience_promise}</p>
            </div>
            {analysis.tone.length > 0 ? (
              <div>
                <p className="text-xs uppercase tracking-wide text-slate-500">Tone</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {analysis.tone.map((t) => (
                    <Badge key={t} tone="info">
                      {t}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : null}
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
              <div>
                <p className="text-slate-500">Personal story</p>
                <p className="text-slate-200">{Math.round(analysis.personal_story_level * 100)}%</p>
              </div>
              <div>
                <p className="text-slate-500">Educational</p>
                <p className="text-slate-200">{Math.round(analysis.educational_level * 100)}%</p>
              </div>
              <div>
                <p className="text-slate-500">Confidence</p>
                <p className="text-slate-200">{Math.round(analysis.confidence * 100)}%</p>
              </div>
              <div>
                <p className="text-slate-500">Sources</p>
                <p className="text-slate-200">
                  {analysis.transcript_available ? "Transcript" : "No transcript"},{" "}
                  {analysis.visual_analysis_available ? "Visual" : "No visual"}
                </p>
              </div>
            </div>
          </Card>
        ) : (
          <Card>
            <p className="text-slate-400">{strings.posts.noAnalysis}</p>
          </Card>
        )}
      </div>
    </div>
  );
}
