"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { strings } from "@/lib/strings";

const links = [
  { href: "/", label: strings.nav.inspiration },
  { href: "/ideas", label: strings.nav.ideas },
  { href: "/todo", label: strings.nav.todo },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-10 border-b border-fuchsia-100 bg-white/70 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-center gap-1 px-4 py-3">
        <nav className="flex gap-1 text-sm">
          {links.map((link) => {
            const active = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 transition-colors ${
                  active
                    ? "bg-purple-100 text-purple-700"
                    : "text-gray-500 hover:bg-pink-50 hover:text-gray-700"
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
