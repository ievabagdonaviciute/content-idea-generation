"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { strings } from "@/lib/strings";
import { Card } from "@/components/Card";
import { Badge, noveltyTone, similarityTone } from "@/components/Badge";
import { ErrorView, LoadingView } from "@/components/StateViews";
import { FEEDBACK_RATINGS, SCRIPT_MODES, type FeedbackRating } from "@/types/ideas";

export default function IdeaDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [comment, setComment] = useState("");
  const [selectedRating, setSelectedRating] = useState<FeedbackRating | null>(null);
  const [scriptMode, setScriptMode] = useState(SCRIPT_MODES[0].value);

  const ideaQuery = useQuery({
    queryKey: ["ideas", params.id],
    queryFn: () => api.getIdea(params.id),
  });

  const briefQuery = useQuery({
    queryKey: ["ideas", params.id, "brief"],
    queryFn: () => api.getBrief(params.id),
    retry: false,
  });
  const scriptQuery = useQuery({
    queryKey: ["ideas", params.id, "script"],
    queryFn: () => api.getScript(params.id),
    retry: false,
  });

  const feedback = useMutation({
    mutationFn: () => api.submitIdeaFeedback(params.id, { rating: selectedRating!, comment: comment || null }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ideas", params.id] }),
  });

  const generateBrief = useMutation({
    mutationFn: () => api.generateBrief(params.id),
    onSuccess: (data) => queryClient.setQueryData(["ideas", params.id, "brief"], data),
  });

  const generateScript = useMutation({
    mutationFn: () => api.generateScript(params.id, { mode: scriptMode }),
    onSuccess: (data) => queryClient.setQueryData(["ideas", params.id, "script"], data),
  });

  if (ideaQuery.isError) {
    return <ErrorView error={ideaQuery.error} onRetry={() => ideaQuery.refetch()} />;
  }
  if (!ideaQuery.data) {
    return <LoadingView />;
  }

  const idea = ideaQuery.data;
  const brief = briefQuery.data ?? generateBrief.data;
  const script = scriptQuery.data ?? generateScript.data;
  const briefMissing = briefQuery.error instanceof ApiError && briefQuery.error.status === 404;
  const scriptMissing = scriptQuery.error instanceof ApiError && scriptQuery.error.status === 404;

  return (
    <div className="space-y-6">
      <Link href="/ideas" className="text-sm text-brand-300 hover:underline">
        ← {strings.common.back}
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{idea.title}</h1>
          <p className="mt-1 text-slate-400">
            {idea.content_pillar} · {idea.format_label_lt} · {idea.suggested_duration_seconds}s
          </p>
        </div>
        <div className="flex shrink-0 gap-1.5">
          <Badge tone={noveltyTone(idea.novelty_level)}>{strings.ideas.novelty[idea.novelty_level]}</Badge>
          <Badge tone={similarityTone(idea.similarity_category)}>
            {strings.ideas.similarity[idea.similarity_category]}
          </Badge>
        </div>
      </div>

      <Card className="space-y-4">
        <p className="text-slate-200">{idea.concept}</p>
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Why it fits me</p>
          <p className="text-slate-300">{idea.why_it_fits_me}</p>
        </div>
        {idea.inspiration_pattern ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Inspiration pattern</p>
            <p className="text-slate-300">{idea.inspiration_pattern}</p>
          </div>
        ) : null}
        {idea.originality_note ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Originality note</p>
            <p className="text-slate-300">{idea.originality_note}</p>
          </div>
        ) : null}
        {idea.closest_existing_post_id ? (
          <Link
            href={`/posts/${idea.closest_existing_post_id}`}
            className="inline-block text-sm text-brand-300 hover:underline"
          >
            View closest existing post (similarity {Math.round(idea.similarity_score * 100)}%)
          </Link>
        ) : null}
        <div>
          <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">{strings.ideas.hookOptions}</p>
          <ul className="space-y-1 text-sm text-slate-300">
            {idea.hook_options.map((hook, i) => (
              <li key={i}>&ldquo;{hook}&rdquo;</li>
            ))}
          </ul>
        </div>
        {idea.outline.length > 0 ? (
          <div>
            <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">{strings.ideas.outline}</p>
            <ol className="list-inside list-decimal space-y-1 text-sm text-slate-300">
              {idea.outline.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>
        ) : null}
      </Card>

      <Card className="space-y-3">
        <h2 className="text-sm font-medium text-slate-300">{strings.ideas.feedback}</h2>
        <div className="flex flex-wrap gap-2">
          {FEEDBACK_RATINGS.map((r) => (
            <button
              key={r.value}
              onClick={() => setSelectedRating(r.value)}
              className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
                selectedRating === r.value
                  ? "border-brand-500 bg-brand-500/20 text-brand-200"
                  : "border-slate-700 text-slate-300 hover:bg-slate-800"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder={strings.ideas.feedbackComment}
          rows={2}
          className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-slate-100"
        />
        <button
          onClick={() => feedback.mutate()}
          disabled={!selectedRating || feedback.isPending}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >
          {strings.ideas.submitFeedback}
        </button>
        {feedback.isError ? <ErrorView error={feedback.error} /> : null}
        {feedback.isSuccess ? <p className="text-sm text-emerald-400">Feedback saved.</p> : null}
      </Card>

      <Card className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-300">{strings.ideas.brief}</h2>
          <button
            onClick={() => generateBrief.mutate()}
            disabled={generateBrief.isPending}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
          >
            {generateBrief.isPending
              ? strings.ideas.generatingBrief
              : brief
                ? "Regenerate brief"
                : strings.ideas.generateBrief}
          </button>
        </div>
        {generateBrief.isError ? <ErrorView error={generateBrief.error} /> : null}
        {!brief && briefQuery.isLoading && !briefMissing ? <LoadingView /> : null}
        {brief ? (
          <div className="space-y-3 text-sm">
            <p className="text-slate-200">
              <span className="text-slate-500">Objective: </span>
              {brief.objective}
            </p>
            <p className="text-slate-200">
              <span className="text-slate-500">Target viewer: </span>
              {brief.target_viewer}
            </p>
            <p className="text-slate-200">
              <span className="text-slate-500">Promise: </span>
              {brief.promise}
            </p>
            <div>
              <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">Beats</p>
              <ol className="list-inside list-decimal space-y-1 text-slate-300">
                {brief.beats.map((beat, i) => (
                  <li key={i}>
                    <span className="font-medium text-slate-200">{beat.label}:</span> {beat.description}
                  </li>
                ))}
              </ol>
            </div>
            <p className="text-slate-200">
              <span className="text-slate-500">Closing line: </span>
              {brief.closing_line}
            </p>
            <p className="text-slate-200">
              <span className="text-slate-500">CTA: </span>
              {brief.call_to_action}
            </p>
            {brief.hashtags.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {brief.hashtags.map((tag) => (
                  <Badge key={tag} tone="info">
                    #{tag}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}
      </Card>

      <Card className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-medium text-slate-300">{strings.ideas.script}</h2>
          <div className="flex items-center gap-2">
            <select
              value={scriptMode}
              onChange={(e) => setScriptMode(e.target.value)}
              className="rounded-md border border-slate-700 bg-slate-950 px-2 py-1.5 text-sm text-slate-200"
            >
              {SCRIPT_MODES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
            <button
              onClick={() => generateScript.mutate()}
              disabled={generateScript.isPending}
              className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800 disabled:opacity-50"
            >
              {generateScript.isPending
                ? strings.ideas.generatingScript
                : script
                  ? "Regenerate script"
                  : strings.ideas.generateScript}
            </button>
          </div>
        </div>
        {generateScript.isError ? <ErrorView error={generateScript.error} /> : null}
        {!script && scriptQuery.isLoading && !scriptMissing ? <LoadingView /> : null}
        {script ? (
          <div className="space-y-3 text-sm">
            <p className="text-slate-500">
              Mode: {script.mode} · ~{script.estimated_duration_seconds}s
            </p>
            <div className="space-y-2 rounded-md bg-slate-950/60 p-3">
              {script.spoken_lines.map((line, i) => (
                <p key={i} className="text-slate-200">
                  {line}
                </p>
              ))}
            </div>
            {script.placeholders.length > 0 ? (
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">Fill in yourself</p>
                <ul className="list-inside list-disc space-y-1 text-amber-300">
                  {script.placeholders.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {script.editing_notes.length > 0 ? (
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">Editing notes</p>
                <ul className="list-inside list-disc space-y-1 text-slate-400">
                  {script.editing_notes.map((n, i) => (
                    <li key={i}>{n}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </Card>
    </div>
  );
}
