import Link from "next/link";

export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-xl border border-fuchsia-100 bg-white/80 p-4 shadow-sm shadow-fuchsia-100/50 backdrop-blur ${className}`}
    >
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
      className={`block rounded-xl border border-fuchsia-100 bg-white/80 p-4 shadow-sm shadow-fuchsia-100/50 backdrop-blur transition-colors hover:border-purple-300 hover:bg-white ${className}`}
    >
      {children}
    </Link>
  );
}
