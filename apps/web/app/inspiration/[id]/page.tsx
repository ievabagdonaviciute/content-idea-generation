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
      <Link href="/inspiration" className="text-sm text-brand-300 hover:underline">
        ← {strings.common.back}
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{strings.inspiration.detailTitle}</h1>
          <a
            href={item.tiktok_url}
            target="_blank"
            rel="noreferrer"
            className="mt-1 block text-sm text-brand-300 hover:underline"
          >
            {item.tiktok_url}
          </a>
        </div>
        <Badge tone={NOTION_STATUS_TONE[item.notion_status] ?? "neutral"}>{item.notion_status}</Badge>
      </div>

      <Card className="space-y-3">
        <p className="text-slate-200">{item.title || "—"}</p>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-slate-500">Creator</dt>
            <dd className="text-slate-300">{item.creator_name || "—"}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Availability</dt>
            <dd className="text-slate-300">
              {item.availability ? strings.inspiration.availability[item.availability] : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Format hint</dt>
            <dd className="text-slate-300">{item.format_hint || "—"}</dd>
          </div>
        </dl>
        {item.note_why_saved ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Why I saved it</p>
            <p className="text-slate-200">{item.note_why_saved}</p>
          </div>
        ) : null}
        {item.note_favorite_part ? (
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Favorite part</p>
            <p className="text-slate-200">{item.note_favorite_part}</p>
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

      {item.embed_html ? (
        <Card>
          <div dangerouslySetInnerHTML={{ __html: item.embed_html }} />
        </Card>
      ) : item.thumbnail_url ? (
        <Card>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={item.thumbnail_url} alt={item.title ?? "TikTok thumbnail"} className="rounded-md" />
        </Card>
      ) : null}

      <div>
        <button
          onClick={() => reanalyze.mutate()}
          disabled={reanalyze.isPending}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >
          {reanalyze.isPending
            ? strings.posts.reanalyzing
            : alreadyProcessed
              ? strings.inspiration.reanalyzeAgain
              : strings.inspiration.reanalyze}
        </button>
        {reanalyze.isError ? <ErrorView error={reanalyze.error} /> : null}
      </div>

      {item.error_message ? <ErrorView error={new Error(item.error_message)} /> : null}
    </div>
  );
}
