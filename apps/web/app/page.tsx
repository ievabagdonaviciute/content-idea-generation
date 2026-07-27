"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { strings } from "@/lib/strings";
import { Card, LinkCard } from "@/components/Card";
import { ErrorView, LoadingView } from "@/components/StateViews";

const COUNT_SAMPLE_LIMIT = 200;

function CountBadge({ count, limit }: { count: number; limit: number }) {
  return (
    <p className="text-3xl font-semibold text-slate-100">
      {count}
      {count === limit ? "+" : ""}
    </p>
  );
}

export default function DashboardPage() {
  const queryClient = useQueryClient();

  const postsQuery = useQuery({
    queryKey: ["posts", "count"],
    queryFn: () => api.listPosts(COUNT_SAMPLE_LIMIT, 0),
  });
  const inspirationQuery = useQuery({
    queryKey: ["inspiration", "count"],
    queryFn: () => api.listInspiration(COUNT_SAMPLE_LIMIT, 0),
  });
  const ideasQuery = useQuery({
    queryKey: ["ideas", "count"],
    queryFn: () => api.listIdeas(COUNT_SAMPLE_LIMIT, 0),
  });
  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: api.getProfile,
    retry: false,
  });

  const syncTikTok = useMutation({
    mutationFn: api.syncTikTok,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["posts"] });
    },
  });
  const syncNotion = useMutation({
    mutationFn: api.syncNotion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inspiration"] });
    },
  });

  const profileMissing = profileQuery.error instanceof ApiError && profileQuery.error.status === 404;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-100">{strings.dashboard.title}</h1>
        <p className="mt-1 text-slate-400">{strings.dashboard.subtitle}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <LinkCard href="/posts">
          <p className="text-sm text-slate-400">{strings.dashboard.postsCard}</p>
          {postsQuery.data ? (
            <CountBadge count={postsQuery.data.items.length} limit={COUNT_SAMPLE_LIMIT} />
          ) : postsQuery.isError ? (
            <p className="text-sm text-red-400">{strings.common.error}</p>
          ) : (
            <LoadingView />
          )}
        </LinkCard>

        <LinkCard href="/inspiration">
          <p className="text-sm text-slate-400">{strings.dashboard.inspirationCard}</p>
          {inspirationQuery.data ? (
            <CountBadge count={inspirationQuery.data.items.length} limit={COUNT_SAMPLE_LIMIT} />
          ) : inspirationQuery.isError ? (
            <p className="text-sm text-red-400">{strings.common.error}</p>
          ) : (
            <LoadingView />
          )}
        </LinkCard>

        <LinkCard href="/ideas">
          <p className="text-sm text-slate-400">{strings.dashboard.ideasCard}</p>
          {ideasQuery.data ? (
            <CountBadge count={ideasQuery.data.items.length} limit={COUNT_SAMPLE_LIMIT} />
          ) : ideasQuery.isError ? (
            <p className="text-sm text-red-400">{strings.common.error}</p>
          ) : (
            <LoadingView />
          )}
        </LinkCard>

        <LinkCard href="/profile">
          <p className="text-sm text-slate-400">{strings.dashboard.profileCard}</p>
          {profileQuery.data ? (
            <p className="text-3xl font-semibold text-slate-100">
              {Math.round(profileQuery.data.overall_confidence * 100)}%
            </p>
          ) : profileMissing ? (
            <p className="mt-2 text-sm text-slate-300">{strings.dashboard.noProfileYet}</p>
          ) : profileQuery.isError ? (
            <p className="text-sm text-red-400">{strings.common.error}</p>
          ) : (
            <LoadingView />
          )}
        </LinkCard>
      </div>

      <Card>
        <h2 className="mb-3 text-sm font-medium text-slate-300">{strings.dashboard.quickActions}</h2>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => syncTikTok.mutate()}
            disabled={syncTikTok.isPending}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
          >
            {syncTikTok.isPending ? strings.dashboard.syncing : strings.dashboard.syncTikTok}
          </button>
          <button
            onClick={() => syncNotion.mutate()}
            disabled={syncNotion.isPending}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
          >
            {syncNotion.isPending ? strings.dashboard.syncing : strings.dashboard.syncNotion}
          </button>
          <Link
            href="/ideas"
            className="rounded-md border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800"
          >
            {strings.dashboard.generateIdeas}
          </Link>
        </div>
        {syncTikTok.isError ? <ErrorView error={syncTikTok.error} /> : null}
        {syncTikTok.data ? (
          <p className="mt-3 text-sm text-slate-400">
            TikTok sync {syncTikTok.data.status}: {syncTikTok.data.items_processed} processed.
          </p>
        ) : null}
        {syncNotion.isError ? <ErrorView error={syncNotion.error} /> : null}
        {syncNotion.data ? (
          <p className="mt-3 text-sm text-slate-400">
            Notion sync {syncNotion.data.status}: {syncNotion.data.items_processed} processed,{" "}
            {syncNotion.data.items_failed} failed.
          </p>
        ) : null}
      </Card>
    </div>
  );
}
