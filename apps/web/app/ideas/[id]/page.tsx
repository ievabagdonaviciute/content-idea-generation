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
  const mediaQuery = useQuery({
    queryKey: ["ideas", params.id, "media"],
    queryFn: () => api.getIdeaMedia(params.id),
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

  const generateMedia = useMutation({
    mutationFn: () => api.generateIdeaMedia(params.id),
    onSuccess: (data) => queryClient.setQueryData(["ideas", params.id, "media"], data),
  });

  const addToTodo = useMutation({
    mutationFn: () => api.setIdeaStatus(params.id, "saved"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ideas", params.id] }),
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
  const media = mediaQuery.data ?? generateMedia.data;
  const briefMissing = briefQuery.error instanceof ApiError && briefQuery.error.status === 404;
  const scriptMissing = scriptQuery.error instanceof ApiError && scriptQuery.error.status === 404;
  const mediaMissing = mediaQuery.error instanceof ApiError && mediaQuery.error.status === 404;

  return (
    <div className="space-y-6">
      <Link href="/ideas" className="text-sm text-purple-600 hover:underline">
        ← {strings.common.back}
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">{idea.title}</h1>
          <p className="mt-1 text-gray-500">
            {idea.content_pillar} · {idea.format_label_lt} · {idea.suggested_duration_seconds}s
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-1.5">
          <Badge tone={noveltyTone(idea.novelty_level)}>{strings.ideas.novelty[idea.novelty_level]}</Badge>
          <Badge tone={similarityTone(idea.similarity_category)}>
            {strings.ideas.similarity[idea.similarity_category]}
          </Badge>
          {idea.status === "proposed" ? (
            <button
              onClick={() => addToTodo.mutate()}
              disabled={addToTodo.isPending}
              className="rounded-md border border-purple-200 px-2.5 py-1 text-xs font-medium text-purple-700 hover:bg-purple-50 disabled:opacity-50"
            >
              {addToTodo.isPending ? strings.ideas.addingToTodo : strings.ideas.addToTodo}
            </button>
          ) : (
            <Badge tone={idea.status === "done" ? "success" : "brand"}>
              {strings.ideas.status[idea.status]}
            </Badge>
          )}
        </div>
      </div>
      {addToTodo.isError ? <ErrorView error={addToTodo.error} /> : null}

      <Card className="space-y-4">
        <p className="text-gray-800">{idea.concept}</p>
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-400">Why it fits me</p>
          <p className="text-gray-700">{idea.why_it_fits_me}</p>
        </div>
        {idea.inspiration_pattern ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-400">Inspiration pattern</p>
            <p className="text-gray-700">{idea.inspiration_pattern}</p>
          </div>
        ) : null}
        {idea.originality_note ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-400">Originality note</p>
            <p className="text-gray-700">{idea.originality_note}</p>
          </div>
        ) : null}
        <div>
          <p className="mb-1 text-xs uppercase tracking-wide text-gray-400">{strings.ideas.hookOptions}</p>
          <ul className="space-y-1 text-sm text-gray-700">
            {idea.hook_options.map((hook, i) => (
              <li key={i}>&ldquo;{hook}&rdquo;</li>
            ))}
          </ul>
        </div>
        {idea.outline.length > 0 ? (
          <div>
            <p className="mb-1 text-xs uppercase tracking-wide text-gray-400">{strings.ideas.outline}</p>
            <ol className="list-inside list-decimal space-y-1 text-sm text-gray-700">
              {idea.outline.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>
        ) : null}
      </Card>

      <Card className="space-y-3">
        <h2 className="text-sm font-medium text-gray-700">{strings.ideas.feedback}</h2>
        <div className="flex flex-wrap gap-2">
          {FEEDBACK_RATINGS.map((r) => (
            <button
              key={r.value}
              onClick={() => setSelectedRating(r.value)}
              className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
                selectedRating === r.value
                  ? "border-purple-400 bg-purple-100 text-purple-700"
                  : "border-fuchsia-200 text-gray-600 hover:bg-pink-50"
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
          className="w-full rounded-md border border-fuchsia-200 bg-white px-3 py-1.5 text-sm text-gray-900"
        />
        <button
          onClick={() => feedback.mutate()}
          disabled={!selectedRating || feedback.isPending}
          className="rounded-md bg-gradient-to-r from-pink-500 to-purple-600 px-4 py-2 text-sm font-medium text-white hover:from-pink-600 hover:to-purple-700 disabled:opacity-50"
        >
          {strings.ideas.submitFeedback}
        </button>
        {feedback.isError ? <ErrorView error={feedback.error} /> : null}
        {feedback.isSuccess ? <p className="text-sm text-emerald-600">Feedback saved.</p> : null}
      </Card>

      <Card className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-700">{strings.ideas.brief}</h2>
          <button
            onClick={() => generateBrief.mutate()}
            disabled={generateBrief.isPending}
            className="rounded-md border border-purple-200 px-3 py-1.5 text-sm text-purple-700 hover:bg-purple-50 disabled:opacity-50"
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
            <p className="text-gray-800">
              <span className="text-gray-400">Objective: </span>
              {brief.objective}
            </p>
            <p className="text-gray-800">
              <span className="text-gray-400">Target viewer: </span>
              {brief.target_viewer}
            </p>
            <p className="text-gray-800">
              <span className="text-gray-400">Promise: </span>
              {brief.promise}
            </p>
            <div>
              <p className="mb-1 text-xs uppercase tracking-wide text-gray-400">Beats</p>
              <ol className="list-inside list-decimal space-y-1 text-gray-700">
                {brief.beats.map((beat, i) => (
                  <li key={i}>
                    <span className="font-medium text-gray-800">{beat.label}:</span> {beat.description}
                  </li>
                ))}
              </ol>
            </div>
            <p className="text-gray-800">
              <span className="text-gray-400">Closing line: </span>
              {brief.closing_line}
            </p>
            <p className="text-gray-800">
              <span className="text-gray-400">CTA: </span>
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
          <h2 className="text-sm font-medium text-gray-700">{strings.ideas.script}</h2>
          <div className="flex items-center gap-2">
            <select
              value={scriptMode}
              onChange={(e) => setScriptMode(e.target.value)}
              className="rounded-md border border-fuchsia-200 bg-white px-2 py-1.5 text-sm text-gray-700"
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
              className="rounded-md border border-purple-200 px-3 py-1.5 text-sm text-purple-700 hover:bg-purple-50 disabled:opacity-50"
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
            <p className="text-gray-400">
              Mode: {script.mode} · ~{script.estimated_duration_seconds}s
            </p>
            <div className="space-y-2 rounded-md bg-fuchsia-50/60 p-3">
              {script.spoken_lines.map((line, i) => (
                <p key={i} className="text-gray-800">
                  {line}
                </p>
              ))}
            </div>
            {script.placeholders.length > 0 ? (
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-gray-400">Fill in yourself</p>
                <ul className="list-inside list-disc space-y-1 text-amber-600">
                  {script.placeholders.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </div>
            ) : null}
            {script.editing_notes.length > 0 ? (
              <div>
                <p className="mb-1 text-xs uppercase tracking-wide text-gray-400">Editing notes</p>
                <ul className="list-inside list-disc space-y-1 text-gray-500">
                  {script.editing_notes.map((n, i) => (
                    <li key={i}>{n}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </Card>

      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-gray-700">{strings.ideas.sourceMedia}</h2>
          <button
            onClick={() => generateMedia.mutate()}
            disabled={generateMedia.isPending}
            className="rounded-md border border-purple-200 px-3 py-1.5 text-sm text-purple-700 hover:bg-purple-50 disabled:opacity-50"
          >
            {generateMedia.isPending
              ? strings.ideas.sourcingMedia
              : media
                ? strings.ideas.regenerateMedia
                : strings.ideas.sourceMedia}
          </button>
        </div>
        {generateMedia.isError ? <ErrorView error={generateMedia.error} /> : null}
        {!media && mediaQuery.isLoading && !mediaMissing ? <LoadingView /> : null}
        {media ? (
          <div className="space-y-4">
            <div>
              <p className="mb-2 text-xs uppercase tracking-wide text-gray-400">
                {strings.ideas.images}
              </p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
                {media.images.map((img, i) => (
                  <a
                    key={i}
                    href={img.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="block overflow-hidden rounded-md border border-fuchsia-100"
                    title={img.credit ?? undefined}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={img.thumbnail_url} alt="" className="h-24 w-full object-cover" />
                  </a>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-xs uppercase tracking-wide text-gray-400">
                {strings.ideas.memes}
              </p>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
                {media.memes.map((meme, i) => (
                  <a
                    key={i}
                    href={meme.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block overflow-hidden rounded-md border border-fuchsia-100"
                    title={meme.caption_lines.join(" / ")}
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={meme.url} alt={meme.template_name} className="h-24 w-full object-cover" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </Card>
    </div>
  );
}
