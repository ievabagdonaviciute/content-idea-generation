import { strings } from "@/lib/strings";
import { ApiError } from "@/lib/api";

export function LoadingView({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-10 text-sm text-slate-400">
      <span className="h-3 w-3 animate-pulse rounded-full bg-brand-400" />
      {label ?? strings.common.loading}
    </div>
  );
}

export function EmptyView({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-700 bg-slate-900/40 px-6 py-10 text-center">
      <p className="text-slate-300">{title}</p>
      {hint ? <p className="mt-1 text-sm text-slate-500">{hint}</p> : null}
    </div>
  );
}

export function ErrorView({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : strings.common.error;
  const status = error instanceof ApiError ? error.status : undefined;

  return (
    <div className="rounded-lg border border-red-900/50 bg-red-950/30 px-6 py-6 text-center">
      <p className="text-red-300">
        {strings.common.error}
        {status ? ` (${status})` : ""}
      </p>
      <p className="mt-1 text-sm text-red-400/80">{message}</p>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="mt-3 rounded-md border border-red-800 px-3 py-1.5 text-sm text-red-200 hover:bg-red-900/40"
        >
          {strings.common.retry}
        </button>
      ) : null}
    </div>
  );
}
