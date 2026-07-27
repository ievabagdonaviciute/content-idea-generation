"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { strings } from "@/lib/strings";
import { LinkCard, Card } from "@/components/Card";
import { Badge, noveltyTone, similarityTone } from "@/components/Badge";
import { EmptyView, ErrorView, LoadingView } from "@/components/StateViews";
import type { ContentIdeaOut } from "@/types/ideas";

const PAGE_SIZE = 20;

export default function IdeasPage() {
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const [count, setCount] = useState(3);
  const [contentPillar, setContentPillar] = useState("");
  const [recommendedFormat, setRecommendedFormat] = useState("");
  const [instructions, setInstructions] = useState("");
  const [excludedSubjects, setExcludedSubjects] = useState("");
  const [outputLanguage, setOutputLanguage] = useState("lt");

  const ideasQuery = useQuery({
    queryKey: ["ideas", "list", limit],
    queryFn: () => api.listIdeas(limit, 0),
  });

  const generate = useMutation({
    mutationFn: () =>
      api.generateIdeas({
        count,
        content_pillar: contentPillar || null,
        recommended_format: recommendedFormat || null,
        instructions: instructions || null,
        excluded_subjects: excludedSubjects
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        output_language: outputLanguage || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ideas"] });
      setShowForm(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{strings.ideas.title}</h1>
          <p className="mt-1 text-slate-400">{strings.ideas.subtitle}</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500"
        >
          {strings.ideas.generate}
        </button>
      </div>

      {showForm ? (
        <Card className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block text-sm">
              <span className="mb-1 block text-slate-400">{strings.ideas.count}</span>
              <input
                type="number"
                min={1}
                max={10}
                value={count}
                onChange={(e) => setCount(Number(e.target.value))}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100"
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-slate-400">{strings.ideas.outputLanguage}</span>
              <select
                value={outputLanguage}
                onChange={(e) => setOutputLanguage(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100"
              >
                <option value="lt">Lithuanian</option>
                <option value="en">English</option>
              </select>
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-slate-400">{strings.ideas.contentPillar}</span>
              <input
                value={contentPillar}
                onChange={(e) => setContentPillar(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100"
              />
            </label>
            <label className="block text-sm">
              <span className="mb-1 block text-slate-400">{strings.ideas.format}</span>
              <input
                value={recommendedFormat}
                onChange={(e) => setRecommendedFormat(e.target.value)}
                className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100"
              />
            </label>
          </div>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-400">{strings.ideas.instructions}</span>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-400">{strings.ideas.excludedSubjects}</span>
            <input
              value={excludedSubjects}
              onChange={(e) => setExcludedSubjects(e.target.value)}
              className="w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-1.5 text-slate-100"
            />
          </label>
          <div className="flex items-center gap-3">
            <button
              onClick={() => generate.mutate()}
              disabled={generate.isPending}
              className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
            >
              {generate.isPending ? strings.ideas.generating : strings.ideas.generate}
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="rounded-md border border-slate-700 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
            >
              {strings.common.cancel}
            </button>
          </div>
          {generate.isError ? <ErrorView error={generate.error} /> : null}
        </Card>
      ) : null}

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
                className="w-full rounded-md border border-slate-700 py-2 text-sm text-slate-300 hover:bg-slate-800"
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
  return (
    <LinkCard href={`/ideas/${idea.id}`} className="space-y-2">
      <div className="flex items-start justify-between gap-4">
        <p className="text-slate-100">{idea.title}</p>
        <div className="flex shrink-0 gap-1.5">
          <Badge tone={noveltyTone(idea.novelty_level)}>{strings.ideas.novelty[idea.novelty_level]}</Badge>
          <Badge tone={similarityTone(idea.similarity_category)}>
            {strings.ideas.similarity[idea.similarity_category]}
          </Badge>
        </div>
      </div>
      <p className="line-clamp-2 text-sm text-slate-400">{idea.concept}</p>
      <p className="text-xs text-slate-500">
        {idea.content_pillar} · {idea.format_label_lt}
      </p>
    </LinkCard>
  );
}
