const TONES = {
  neutral: "bg-gray-100 text-gray-600",
  info: "bg-blue-100 text-blue-700",
  success: "bg-emerald-100 text-emerald-700",
  warning: "bg-amber-100 text-amber-700",
  danger: "bg-red-100 text-red-700",
  brand: "bg-purple-100 text-purple-700",
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
