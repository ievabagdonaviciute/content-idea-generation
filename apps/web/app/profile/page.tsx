"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import { strings } from "@/lib/strings";
import { Card } from "@/components/Card";
import { EmptyView, ErrorView, LoadingView } from "@/components/StateViews";

function DistributionList({ rows, labelKey }: { rows: Record<string, unknown>[]; labelKey: string }) {
  if (rows.length === 0) return <p className="text-sm text-slate-500">No data yet.</p>;
  return (
    <ul className="space-y-1.5">
      {rows.map((row, i) => {
        const label = String(row[labelKey] ?? "—");
        const share = typeof row.share === "number" ? row.share : undefined;
        const count = typeof row.count === "number" ? row.count : undefined;
        return (
          <li key={`${label}-${i}`} className="flex items-center gap-3 text-sm">
            <span className="min-w-0 flex-1 truncate text-slate-200">{label}</span>
            {share !== undefined ? (
              <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-brand-500"
                  style={{ width: `${Math.round(share * 100)}%` }}
                />
              </div>
            ) : null}
            <span className="w-14 shrink-0 text-right text-slate-500">
              {count !== undefined ? `${count}×` : ""}
              {share !== undefined ? ` ${Math.round(share * 100)}%` : ""}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export default function ProfilePage() {
  const queryClient = useQueryClient();

  const profileQuery = useQuery({
    queryKey: ["profile"],
    queryFn: api.getProfile,
    retry: false,
  });

  const rebuild = useMutation({
    mutationFn: api.rebuildProfile,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }),
  });

  const profileMissing = profileQuery.error instanceof ApiError && profileQuery.error.status === 404;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">{strings.profile.title}</h1>
          <p className="mt-1 text-slate-400">{strings.profile.subtitle}</p>
        </div>
        <button
          onClick={() => rebuild.mutate()}
          disabled={rebuild.isPending}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-500 disabled:opacity-50"
        >
          {rebuild.isPending
            ? strings.profile.building
            : profileQuery.data
              ? strings.profile.rebuild
              : strings.profile.build}
        </button>
      </div>

      {rebuild.isError ? <ErrorView error={rebuild.error} /> : null}

      {profileQuery.data ? (
        <>
          <Card>
            <div className="flex flex-wrap items-center justify-between gap-4">
              <p className="text-sm text-slate-400">
                {strings.profile.sampleSize} {profileQuery.data.sample_size} analyzed post
                {profileQuery.data.sample_size === 1 ? "" : "s"}
              </p>
              <p className="text-sm text-slate-400">
                {strings.profile.confidence}:{" "}
                <span className="font-medium text-slate-200">
                  {Math.round(profileQuery.data.overall_confidence * 100)}%
                </span>
              </p>
            </div>
            {profileQuery.data.observations_lt.length > 0 ? (
              <ul className="mt-4 space-y-1 text-sm text-slate-300">
                {profileQuery.data.observations_lt.map((o, i) => (
                  <li key={i}>• {o}</li>
                ))}
              </ul>
            ) : null}
            {profileQuery.data.confidence_notes.length > 0 ? (
              <ul className="mt-3 space-y-1 text-sm text-slate-500">
                {profileQuery.data.confidence_notes.map((n, i) => (
                  <li key={i}>{n}</li>
                ))}
              </ul>
            ) : null}
          </Card>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card>
              <h2 className="mb-3 text-sm font-medium text-slate-300">{strings.profile.pillars}</h2>
              <DistributionList rows={profileQuery.data.content_pillars} labelKey="topic" />
            </Card>
            <Card>
              <h2 className="mb-3 text-sm font-medium text-slate-300">{strings.profile.formats}</h2>
              <DistributionList rows={profileQuery.data.format_distribution} labelKey="format" />
            </Card>
            <Card>
              <h2 className="mb-3 text-sm font-medium text-slate-300">{strings.profile.hooks}</h2>
              <DistributionList rows={profileQuery.data.typical_hooks} labelKey="hook_type" />
            </Card>
            <Card>
              <h2 className="mb-3 text-sm font-medium text-slate-300">{strings.profile.tone}</h2>
              <DistributionList rows={profileQuery.data.tone_distribution} labelKey="tone" />
            </Card>
          </div>

          {profileQuery.data.underused_formats.length > 0 || profileQuery.data.content_gaps.length > 0 ? (
            <Card>
              <h2 className="mb-2 text-sm font-medium text-slate-300">{strings.profile.gaps}</h2>
              <div className="flex flex-wrap gap-1.5">
                {profileQuery.data.content_gaps.map((gap) => (
                  <span
                    key={gap}
                    className="rounded-full bg-amber-500/15 px-2.5 py-0.5 text-xs text-amber-300"
                  >
                    {gap}
                  </span>
                ))}
              </div>
            </Card>
          ) : null}
        </>
      ) : profileMissing ? (
        <EmptyView title={strings.profile.empty} hint={strings.profile.emptyHint} />
      ) : profileQuery.isError ? (
        <ErrorView error={profileQuery.error} onRetry={() => profileQuery.refetch()} />
      ) : (
        <LoadingView />
      )}
    </div>
  );
}
