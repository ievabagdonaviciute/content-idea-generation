"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { strings } from "@/lib/strings";
import { Card } from "@/components/Card";
import { Badge, noveltyTone, similarityTone } from "@/components/Badge";
import { EmptyView, ErrorView, LoadingView } from "@/components/StateViews";
import type { ContentIdeaOut } from "@/types/ideas";

const PAGE_SIZE = 20;

export default function IdeasPage() {
  const [limit, setLimit] = useState(PAGE_SIZE);
  const queryClient = useQueryClient();

  const [count, setCount] = useState(3);
  const [instructions, setInstructions] = useState("");
  const [outputLanguage, setOutputLanguage] = useState("lt");

  const ideasQuery = useQuery({
    queryKey: ["ideas", "list", limit],
    queryFn: () => api.listIdeas(limit, 0),
  });

  const generate = useMutation({
    mutationFn: () =>
      api.generateIdeas({
        count,
        instructions: instructions || null,
        output_language: outputLanguage || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ideas"] });
      setInstructions("");
    },
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">{strings.ideas.title}</h1>
        <p className="mt-1 text-gray-500">{strings.ideas.subtitle}</p>
      </div>

      <Card className="space-y-3">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-[auto_1fr_auto]">
          <label className="block text-sm">
            <span className="mb-1 block text-gray-500">{strings.ideas.count}</span>
            <input
              type="number"
              min={1}
              max={10}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              className="w-20 rounded-md border border-fuchsia-200 bg-white px-3 py-1.5 text-gray-900"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-500">{strings.ideas.instructions}</span>
            <input
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="e.g. something about AI safety"
              className="w-full rounded-md border border-fuchsia-200 bg-white px-3 py-1.5 text-gray-900"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-gray-500">{strings.ideas.outputLanguage}</span>
            <select
              value={outputLanguage}
              onChange={(e) => setOutputLanguage(e.target.value)}
              className="rounded-md border border-fuchsia-200 bg-white px-3 py-1.5 text-gray-900"
            >
              <option value="lt">Lithuanian</option>
              <option value="en">English</option>
            </select>
          </label>
        </div>
        <button
          onClick={() => generate.mutate()}
          disabled={generate.isPending}
          className="rounded-md bg-gradient-to-r from-pink-500 to-purple-600 px-4 py-2 text-sm font-medium text-white hover:from-pink-600 hover:to-purple-700 disabled:opacity-50"
        >
          {generate.isPending ? strings.ideas.generating : strings.ideas.generate}
        </button>
        {generate.isError ? <ErrorView error={generate.error} /> : null}
      </Card>

      {ideasQuery.data ? (
        ideasQuery.data.items.length === 0 ? (
          <EmptyView title={strings.ideas.empty} />
        ) : (
          <div className="space-y-3">
            {ideasQuery.data.items.map((idea) => (
              <IdeaRow key={idea.id} idea={idea} />
            ))}
            {ideasQuery.data.items.length === limit ? (
              <button
                onClick={() => setLimit((l) => l + PAGE_SIZE)}
                className="w-full rounded-md border border-purple-200 py-2 text-sm text-purple-700 hover:bg-purple-50"
              >
                {strings.common.loadMore}
              </button>
            ) : null}
          </div>
        )
      ) : ideasQuery.isError ? (
        <ErrorView error={ideasQuery.error} onRetry={() => ideasQuery.refetch()} />
      ) : (
        <LoadingView />
      )}
    </div>
  );
}

function IdeaRow({ idea }: { idea: ContentIdeaOut }) {
  const queryClient = useQueryClient();

  const addToTodo = useMutation({
    mutationFn: () => api.setIdeaStatus(idea.id, "saved"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["ideas"] }),
  });

  return (
    <Card className="space-y-2">
      <Link href={`/ideas/${idea.id}`} className="block space-y-2">
        <div className="flex items-start justify-between gap-4">
          <p className="text-gray-900">{idea.title}</p>
          <div className="flex shrink-0 gap-1.5">
            <Badge tone={noveltyTone(idea.novelty_level)}>{strings.ideas.novelty[idea.novelty_level]}</Badge>
            <Badge tone={similarityTone(idea.similarity_category)}>
              {strings.ideas.similarity[idea.similarity_category]}
            </Badge>
          </div>
        </div>
        <p className="line-clamp-2 text-sm text-gray-500">{idea.concept}</p>
      </Link>
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs text-gray-400">
          {idea.content_pillar} · {idea.format_label_lt}
        </p>
        {idea.status === "proposed" ? (
          <button
            onClick={() => addToTodo.mutate()}
            disabled={addToTodo.isPending}
            className="shrink-0 rounded-md border border-purple-200 px-2.5 py-1 text-xs font-medium text-purple-700 hover:bg-purple-50 disabled:opacity-50"
          >
            {addToTodo.isPending ? strings.ideas.addingToTodo : strings.ideas.addToTodo}
          </button>
        ) : (
          <Badge tone={idea.status === "done" ? "success" : "brand"}>
            {strings.ideas.status[idea.status]}
          </Badge>
        )}
      </div>
    </Card>
  );
}
