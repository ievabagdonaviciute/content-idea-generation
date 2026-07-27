"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { APP_NAME } from "@/lib/config";
import { strings } from "@/lib/strings";

const links = [
  { href: "/", label: strings.nav.dashboard },
  { href: "/posts", label: strings.nav.posts },
  { href: "/inspiration", label: strings.nav.inspiration },
  { href: "/profile", label: strings.nav.profile },
  { href: "/ideas", label: strings.nav.ideas },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-10">
      <div className="mx-auto flex max-w-5xl items-center gap-6 px-4 py-3">
        <Link href="/" className="font-semibold text-lg text-brand-300">
          {APP_NAME}
        </Link>
        <nav className="flex gap-1 text-sm">
          {links.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 transition-colors ${
                  active
                    ? "bg-brand-500/20 text-brand-200"
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
