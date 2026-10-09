"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

const links = [
  { href: "/studio", label: "Studio" },
  { href: "/validate", label: "Validate" },
  { href: "/dashboard", label: "Accuracy" },
  { href: "/corpus", label: "Corpus" },
  { href: "/history", label: "History" },
  { href: "/docs", label: "Docs" },
  { href: "/settings", label: "Status" },
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-ink text-paper">
      <header className="border-b border-line">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-5 gap-y-1 px-4">
          <Link href="/" className="rounded-sm py-2.5 text-sm font-semibold tracking-tight">
            Q2Py Forge
          </Link>
          <nav aria-label="Primary" className="flex flex-wrap text-sm">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "border-b-2 border-transparent px-2.5 py-2.5 text-muted hover:text-paper",
                    active && "border-amber text-paper",
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
