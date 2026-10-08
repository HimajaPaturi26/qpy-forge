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
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3">
          <Link href="/" className="font-semibold tracking-tight">
            Q2Py Studio
          </Link>
          <nav aria-label="Primary" className="flex flex-wrap gap-1 text-sm">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "rounded-md px-2.5 py-1.5 text-muted hover:bg-white/5 hover:text-paper",
                    active && "bg-white/10 text-paper",
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
    </div>
  );
}
