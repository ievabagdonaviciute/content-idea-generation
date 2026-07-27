"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { strings } from "@/lib/strings";
import { Card } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { ErrorView, LoadingView } from "@/components/StateViews";

const NOTION_STATUS_TONE: Record<string, "neutral" | "info" | "success" | "danger"> = {
  New: "neutral",
  Processing: "info",
  Processed: "success",
  Failed: "danger",
};

export default function InspirationDetailPage() {
  const params = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const itemQuery = useQuery({
    queryKey: ["inspiration", params.id],
    queryFn: () => api.getInspirationItem(params.id),
  });

  const reanalyze = useMutation({
    mutationFn: () => api.reanalyzeInspirationItem(params.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspiration"] }),
  });

  const markUsed = useMutation({
    mutationFn: () => api.markInspirationUsed(params.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspiration"] }),
  });
  const unmarkUsed = useMutation({
    mutationFn: () => api.unmarkInspirationUsed(params.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspiration"] }),
  });

  if (itemQuery.isError) {
    return <ErrorView error={itemQuery.error} onRetry={() => itemQuery.refetch()} />;
  }
  if (!itemQuery.data) {
    return <LoadingView />;
  }

  const item = itemQuery.data;
  const alreadyProcessed = item.notion_status === "Processed";

  return (
    <div className="space-y-6">
      <Link href="/" className="text-sm text-purple-600 hover:underline">
        ← {strings.common.back}
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">{strings.inspiration.detailTitle}</h1>
          <a
            href={item.tiktok_url}
            target="_blank"
            rel="noreferrer"
            className="mt-1 block text-sm text-purple-600 hover:underline"
          >
            {item.tiktok_url}
          </a>
        </div>
        <div className="flex shrink-0 gap-1.5">
          {item.already_used ? <Badge tone="brand">{strings.inspiration.usedBadge}</Badge> : null}
          <Badge tone={NOTION_STATUS_TONE[item.notion_status] ?? "neutral"}>{item.notion_status}</Badge>
        </div>
      </div>

      <Card className="space-y-3">
        <p className="text-gray-800">{item.title || "—"}</p>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-gray-400">Creator</dt>
            <dd className="text-gray-700">{item.creator_name || "—"}</dd>
          </div>
          <div>
            <dt className="text-gray-400">Availability</dt>
            <dd className="text-gray-700">
              {item.availability ? strings.inspiration.availability[item.availability] : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-gray-400">Format hint</dt>
            <dd className="text-gray-700">{item.format_hint || "—"}</dd>
          </div>
        </dl>
        {item.note_why_saved ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-400">Why I saved it</p>
            <p className="text-gray-800">{item.note_why_saved}</p>
          </div>
        ) : null}
        {item.note_favorite_part ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-400">Favorite part</p>
            <p className="text-gray-800">{item.note_favorite_part}</p>
          </div>
        ) : null}
        {item.topics && item.topics.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {item.topics.map((topic) => (
              <Badge key={topic}>{topic}</Badge>
            ))}
          </div>
        ) : null}
      </Card>

      {item.thumbnail_url ? (
        <Card>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={item.thumbnail_url} alt={item.title ?? "TikTok thumbnail"} className="rounded-md" />
        </Card>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <button
          onClick={() => reanalyze.mutate()}
          disabled={reanalyze.isPending}
          className="rounded-md bg-gradient-to-r from-pink-500 to-purple-600 px-4 py-2 text-sm font-medium text-white hover:from-pink-600 hover:to-purple-700 disabled:opacity-50"
        >
          {reanalyze.isPending
            ? strings.common.analyzing
            : alreadyProcessed
              ? strings.inspiration.reanalyzeAgain
              : strings.inspiration.reanalyze}
        </button>
        {item.already_used ? (
          <button
            onClick={() => unmarkUsed.mutate()}
            disabled={unmarkUsed.isPending}
            className="rounded-md border border-purple-200 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-50 disabled:opacity-50"
          >
            {strings.inspiration.unmarkUsed}
          </button>
        ) : (
          <button
            onClick={() => markUsed.mutate()}
            disabled={markUsed.isPending}
            className="rounded-md border border-purple-200 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-50 disabled:opacity-50"
          >
            {strings.inspiration.markUsed}
          </button>
        )}
        <Link
          href="/ideas"
          className="rounded-md border border-purple-200 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-50"
        >
          {strings.dashboard.generateIdeas}
        </Link>
      </div>
      {item.already_used ? <p className="text-xs text-gray-400">{strings.inspiration.usedHint}</p> : null}
      {reanalyze.isError ? <ErrorView error={reanalyze.error} /> : null}
      {markUsed.isError ? <ErrorView error={markUsed.error} /> : null}
      {unmarkUsed.isError ? <ErrorView error={unmarkUsed.error} /> : null}

      {item.error_message ? <ErrorView error={new Error(item.error_message)} /> : null}
    </div>
  );
}
