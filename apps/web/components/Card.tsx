import Link from "next/link";

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg border border-slate-800 bg-slate-900/60 p-4 ${className}`}>
      {children}
    </div>
  );
}

export function LinkCard({
  href,
  children,
  className = "",
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={`block rounded-lg border border-slate-800 bg-slate-900/60 p-4 transition-colors hover:border-brand-600/60 hover:bg-slate-900 ${className}`}
    >
      {children}
    </Link>
  );
}
