"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { strings } from "@/lib/strings";
import { Card } from "@/components/Card";
import { EmptyView, ErrorView, LoadingView } from "@/components/StateViews";
import type { ContentIdeaOut } from "@/types/ideas";

export default function TodoPage() {
  const todoQuery = useQuery({
    queryKey: ["ideas", "list", "saved"],
    queryFn: () => api.listIdeas(50, 0, "saved"),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">{strings.todo.title}</h1>
        <p className="mt-1 text-gray-500">{strings.todo.subtitle}</p>
        <p className="mt-1 text-xs text-gray-400">{strings.todo.doneHint}</p>
      </div>

      {todoQuery.data ? (
        todoQuery.data.items.length === 0 ? (
          <EmptyView title={strings.todo.empty} />
        ) : (
          <div className="space-y-3">
            {todoQuery.data.items.map((idea) => (
              <TodoRow key={idea.id} idea={idea} />
            ))}
          </div>
        )
      ) : todoQuery.isError ? (
        <ErrorView error={todoQuery.error} onRetry={() => todoQuery.refetch()} />
      ) : (
        <LoadingView />
      )}
    </div>
  );
}

function TodoRow({ idea }: { idea: ContentIdeaOut }) {
  const queryClient = useQueryClient();

  const markDone = useMutation({
    mutationFn: () => api.setIdeaStatus(idea.id, "done"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ideas"] });
      queryClient.invalidateQueries({ queryKey: ["inspiration"] });
    },
  });

  return (
    <Card className="space-y-2">
      <Link href={`/ideas/${idea.id}`} className="block space-y-1">
        <p className="text-gray-900">{idea.title}</p>
        <p className="line-clamp-2 text-sm text-gray-500">{idea.concept}</p>
      </Link>
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs text-gray-400">
          {idea.content_pillar} · {idea.format_label_lt} · {idea.suggested_duration_seconds}s
        </p>
        <button
          onClick={() => markDone.mutate()}
          disabled={markDone.isPending}
          className="shrink-0 rounded-md bg-gradient-to-r from-pink-500 to-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:from-pink-600 hover:to-purple-700 disabled:opacity-50"
        >
          {markDone.isPending ? strings.todo.markingDone : strings.todo.markDone}
        </button>
      </div>
      {markDone.isError ? <ErrorView error={markDone.error} /> : null}
    </Card>
  );
}
