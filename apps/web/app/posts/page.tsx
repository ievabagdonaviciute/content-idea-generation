"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { strings } from "@/lib/strings";
import { LinkCard } from "@/components/Card";
import { Badge, processingStatusTone } from "@/components/Badge";
import { EmptyView, ErrorView, LoadingView } from "@/components/StateViews";
import type { OwnPostOut } from "@/types/posts";

const PAGE_SIZE = 20;

export default function PostsPage() {
  const [limit, setLimit] = useState(PAGE_SIZE);
  const queryClient = useQueryClient();

  const postsQuery = useQuery({
    queryKey: ["posts", "list", limit],
    queryFn: () => api.listPosts(limit, 0),
  });

  const syncTikTok = useMutation({
    mutationFn: api.syncTikTok,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["posts"] }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{strings.posts.title}</h1>
          <p className="mt-1 text-slate-400">{strings.posts.subtitle}</p>
        </div>
        <button
          onClick={() => syncTikTok.mutate()}
          disabled={syncTikTok.isPending}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >
          {syncTikTok.isPending ? strings.dashboard.syncing : strings.posts.sync}
        </button>
      </div>

      {syncTikTok.isError ? <ErrorView error={syncTikTok.error} /> : null}

      {postsQuery.data ? (
        postsQuery.data.items.length === 0 ? (
          <EmptyView title={strings.posts.empty} />
        ) : (
          <div className="space-y-3">
            {postsQuery.data.items.map((post) => (
              <PostRow key={post.id} post={post} />
            ))}
            {postsQuery.data.items.length === limit ? (
              <button
                onClick={() => setLimit((l) => l + PAGE_SIZE)}
                className="w-full rounded-md border border-slate-700 py-2 text-sm text-slate-300 hover:bg-slate-800"
              >
                {strings.common.loadMore}
              </button>
            ) : null}
          </div>
        )
      ) : postsQuery.isError ? (
        <ErrorView error={postsQuery.error} onRetry={() => postsQuery.refetch()} />
      ) : (
        <LoadingView />
      )}
    </div>
  );
}

function PostRow({ post }: { post: OwnPostOut }) {
  const video = post.source_video;
  const analysis = post.content_analysis;
  return (
    <LinkCard href={`/posts/${post.id}`} className="flex items-start justify-between gap-4">
      <div className="min-w-0">
        <p className="truncate text-slate-100">{video.caption || video.permalink}</p>
        <p className="mt-1 text-xs text-slate-500">
          {video.posted_at ? new Date(video.posted_at).toLocaleDateString() : "—"}
        </p>
        {analysis ? (
          <p className="mt-2 text-sm text-slate-400">{analysis.primary_topic}</p>
        ) : null}
      </div>
      <Badge tone={processingStatusTone(post.processing_status)}>
        {strings.posts.status[post.processing_status]}
      </Badge>
    </LinkCard>
  );
}
