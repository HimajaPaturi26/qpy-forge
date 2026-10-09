"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useState } from "react";
import { cn } from "@/lib/cn";

const primary = [
  { href: "/studio", label: "Studio" },
  { href: "/validate", label: "Validate" },
];

const explore = [
  { href: "/dashboard", label: "Accuracy" },
  { href: "/corpus", label: "Corpus" },
];

const rest = [
  { href: "/history", label: "History" },
  { href: "/docs", label: "Docs" },
  { href: "/settings", label: "Status" },
];

function active(pathname: string, href: string) {
  return pathname === href;
}

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const menuId = useId();
  const exploreActive = explore.some((link) => active(pathname, link.href));

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) {
      return;
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <div className="min-h-screen bg-ink text-paper">
      <header className="sticky top-0 z-30 border-b border-line bg-ink/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4">
          <Link href="/" className="rounded-sm py-3 text-sm font-semibold tracking-tight">
            Q2Py Forge
          </Link>
          <nav aria-label="Primary" className="ml-2 hidden items-center text-sm md:flex">
            {primary.map((link) => (
              <NavLink key={link.href} href={link.href} current={active(pathname, link.href)}>
                {link.label}
              </NavLink>
            ))}
            <details className="group relative">
              <summary
                className={cn(
                  "cursor-pointer list-none rounded-sm border-b-2 border-transparent px-2.5 py-3 text-muted hover:text-paper [&::-webkit-details-marker]:hidden",
                  exploreActive && "border-amber text-paper",
                )}
              >
                Explore
                <span className="sr-only">{exploreActive ? ", current section" : ""}</span>
              </summary>
              <div className="absolute left-0 z-40 mt-1 min-w-40 rounded-md border border-line bg-panel p-1 shadow-lg">
                {explore.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    aria-current={active(pathname, link.href) ? "page" : undefined}
                    className={cn(
                      "block rounded-sm px-3 py-2 text-muted hover:bg-white/5 hover:text-paper",
                      active(pathname, link.href) && "text-paper",
                    )}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </details>
            {rest.map((link) => (
              <NavLink key={link.href} href={link.href} current={active(pathname, link.href)}>
                {link.label}
              </NavLink>
            ))}
          </nav>
          <Link
            href="/studio"
            className="ml-auto hidden rounded-md bg-amber px-3 py-2 text-sm font-medium text-ink hover:bg-amber/90 md:inline-flex"
          >
            Open Studio
          </Link>
          <button
            type="button"
            className="ml-auto inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-line text-sm md:hidden"
            aria-expanded={open}
            aria-controls={menuId}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? "Close" : "Menu"}
          </button>
        </div>
        {open ? (
          <nav id={menuId} aria-label="Mobile" className="border-t border-line px-4 py-2 md:hidden">
            <ul className="space-y-1 pb-2">
              {primary.map((link) => (
                <MobileLink key={link.href} href={link.href} current={active(pathname, link.href)}>
                  {link.label}
                </MobileLink>
              ))}
              <li className="px-2 pt-3 text-xs text-muted">Explore</li>
              {explore.map((link) => (
                <MobileLink key={link.href} href={link.href} current={active(pathname, link.href)}>
                  {link.label}
                </MobileLink>
              ))}
              {rest.map((link) => (
                <MobileLink key={link.href} href={link.href} current={active(pathname, link.href)}>
                  {link.label}
                </MobileLink>
              ))}
            </ul>
          </nav>
        ) : null}
      </header>
      <main className="mx-auto min-w-0 max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}

function NavLink({ href, current, children }: { href: string; current: boolean; children: ReactNode }) {
  return (
    <Link
      href={href}
      aria-current={current ? "page" : undefined}
      className={cn(
        "border-b-2 border-transparent px-2.5 py-3 text-muted hover:text-paper",
        current && "border-amber text-paper",
      )}
    >
      {children}
    </Link>
  );
}

function MobileLink({ href, current, children }: { href: string; current: boolean; children: ReactNode }) {
  return (
    <li>
      <Link
        href={href}
        aria-current={current ? "page" : undefined}
        className={cn(
          "flex min-h-11 items-center rounded-md px-2 text-base",
          current ? "bg-white/5 text-paper" : "text-muted",
        )}
      >
        {children}
      </Link>
    </li>
  );
}
