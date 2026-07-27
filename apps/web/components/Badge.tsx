const TONES = {
  neutral: "bg-slate-800 text-slate-300",
  info: "bg-blue-500/15 text-blue-300",
  success: "bg-emerald-500/15 text-emerald-300",
  warning: "bg-amber-500/15 text-amber-300",
  danger: "bg-red-500/15 text-red-300",
  brand: "bg-brand-500/20 text-brand-200",
} as const;

export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: keyof typeof TONES;
}) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${TONES[tone]}`}>
      {children}
    </span>
  );
}

export function processingStatusTone(status: string): keyof typeof TONES {
  switch (status) {
    case "completed":
      return "success";
    case "processing":
      return "info";
    case "failed":
      return "danger";
    default:
      return "neutral";
  }
}

export function noveltyTone(level: string): keyof typeof TONES {
  switch (level) {
    case "aligned":
      return "info";
    case "stretch":
      return "warning";
    case "experimental":
      return "brand";
    default:
      return "neutral";
  }
}

export function similarityTone(category: string): keyof typeof TONES {
  switch (category) {
    case "too_similar":
      return "danger";
    case "follow_up":
      return "warning";
    case "related_but_distinct":
      return "info";
    default:
      return "success";
  }
}
