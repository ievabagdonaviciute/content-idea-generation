import { strings } from "@/lib/strings";
import { ApiError } from "@/lib/api";

export function LoadingView({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-10 text-sm text-gray-500">
      <span className="h-3 w-3 animate-pulse rounded-full bg-purple-400" />
      {label ?? strings.common.loading}
    </div>
  );
}

export function EmptyView({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-dashed border-fuchsia-200 bg-white/60 px-6 py-10 text-center">
      <p className="text-gray-600">{title}</p>
      {hint ? <p className="mt-1 text-sm text-gray-400">{hint}</p> : null}
    </div>
  );
}

export function ErrorView({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const message = error instanceof Error ? error.message : strings.common.error;
  const status = error instanceof ApiError ? error.status : undefined;

  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-6 text-center">
      <p className="text-red-600">
        {strings.common.error}
        {status ? ` (${status})` : ""}
      </p>
      <p className="mt-1 text-sm text-red-500/80">{message}</p>
      {onRetry ? (
        <button
          onClick={onRetry}
          className="mt-3 rounded-md border border-red-300 px-3 py-1.5 text-sm text-red-600 hover:bg-red-100"
        >
          {strings.common.retry}
        </button>
      ) : null}
    </div>
  );
}
