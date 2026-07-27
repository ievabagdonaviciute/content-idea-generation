"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { strings } from "@/lib/strings";
import { LinkCard } from "@/components/Card";
import { Badge } from "@/components/Badge";
import { EmptyView, ErrorView, LoadingView } from "@/components/StateViews";
import type { InspirationItemOut } from "@/types/inspiration";

const PAGE_SIZE = 20;

const NOTION_STATUS_TONE: Record<string, "neutral" | "info" | "success" | "danger"> = {
  New: "neutral",
  Processing: "info",
  Processed: "success",
  Failed: "danger",
};

export default function InspirationPage() {
  const [limit, setLimit] = useState(PAGE_SIZE);
  const queryClient = useQueryClient();

  const itemsQuery = useQuery({
    queryKey: ["inspiration", "list", limit],
    queryFn: () => api.listInspiration(limit, 0),
  });

  const syncNotion = useMutation({
    mutationFn: api.syncNotion,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["inspiration"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{strings.inspiration.title}</h1>
          <p className="mt-1 text-slate-400">{strings.inspiration.subtitle}</p>
        </div>
        <button
          onClick={() => syncNotion.mutate()}
          disabled={syncNotion.isPending}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >
          {syncNotion.isPending ? strings.inspiration.syncing : strings.inspiration.sync}
        </button>
      </div>

      {syncNotion.isError ? <ErrorView error={syncNotion.error} /> : null}
      {syncNotion.data ? (
        <p className="text-sm text-slate-400">
          Sync {syncNotion.data.status}: {syncNotion.data.items_processed} processed,{" "}
          {syncNotion.data.items_failed} failed.
        </p>
      ) : null}

      {itemsQuery.data ? (
        itemsQuery.data.items.length === 0 ? (
          <EmptyView title={strings.inspiration.empty} />
        ) : (
          <div className="space-y-3">
            {itemsQuery.data.items.map((item) => (
              <InspirationRow key={item.id} item={item} />
            ))}
            {itemsQuery.data.items.length === limit ? (
              <button
                onClick={() => setLimit((l) => l + PAGE_SIZE)}
                className="w-full rounded-md border border-slate-700 py-2 text-sm text-slate-300 hover:bg-slate-800"
              >
                {strings.common.loadMore}
              </button>
            ) : null}
          </div>
        )
      ) : itemsQuery.isError ? (
        <ErrorView error={itemsQuery.error} onRetry={() => itemsQuery.refetch()} />
      ) : (
        <LoadingView />
      )}
    </div>
  );
}

function InspirationRow({ item }: { item: InspirationItemOut }) {
  return (
    <LinkCard href={`/inspiration/${item.id}`} className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <p className="truncate text-slate-100">{item.title || item.tiktok_url}</p>
        <p className="mt-1 text-xs text-slate-500">
          {item.creator_name ? `@${item.creator_name} · ` : ""}
          {new Date(item.created_at).toLocaleDateString()}
        </p>
        {item.note_why_saved ? (
          <p className="mt-2 truncate text-sm text-slate-400">{item.note_why_saved}</p>
        ) : null}
      </div>
      <Badge tone={NOTION_STATUS_TONE[item.notion_status] ?? "neutral"}>{item.notion_status}</Badge>
    </LinkCard>
  );
}
