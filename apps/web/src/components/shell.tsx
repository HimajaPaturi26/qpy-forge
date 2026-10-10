"use client";

import type { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useId, useRef, useState } from "react";
import { cn } from "@/lib/cn";

const explore = [
  { href: "/dashboard", label: "Accuracy" },
  { href: "/corpus", label: "Corpus" },
];

const rest = [
  { href: "/validate", label: "Validate" },
  { href: "/history", label: "History" },
  { href: "/docs", label: "Docs" },
  { href: "/settings", label: "Status" },
];

const footerLinks = [
  { href: "/studio", label: "Studio" },
  { href: "/validate", label: "Validate" },
  { href: "/dashboard", label: "Accuracy" },
  { href: "/corpus", label: "Corpus" },
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
  const [exploreOpen, setExploreOpen] = useState(false);
  const menuId = useId();
  const exploreId = useId();
  const exploreRef = useRef<HTMLDivElement>(null);
  const exploreActive = explore.some((link) => active(pathname, link.href));
  const studioCurrent = active(pathname, "/studio");

  useEffect(() => {
    setOpen(false);
    setExploreOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open && !exploreOpen) {
      return;
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        setExploreOpen(false);
      }
    }
    function onPointer(event: MouseEvent) {
      if (exploreRef.current && !exploreRef.current.contains(event.target as Node)) {
        setExploreOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onPointer);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onPointer);
    };
  }, [open, exploreOpen]);

  return (
    <div className="flex min-h-screen flex-col bg-ink text-paper">
      <a
        href="#content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded-md focus:bg-amber focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-ink"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-30 border-b border-line bg-panel/95 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center gap-2 px-4">
          <Link href="/" className="rounded-sm py-3 text-sm font-semibold tracking-tight">
            Q2Py Forge
          </Link>
          <nav aria-label="Primary" className="ml-3 hidden items-center text-sm font-semibold md:flex">
            <Link
              href="/studio"
              aria-current={studioCurrent ? "page" : undefined}
              className={cn(
                "mr-1 rounded-md px-3 py-1.5",
                studioCurrent ? "bg-amber text-ink" : "text-amber hover:bg-amber/10 hover:text-amber-hover",
              )}
            >
              Studio
            </Link>
            <div className="relative" ref={exploreRef}>
              <button
                type="button"
                className={cn(
                  "rounded-sm border-b-2 border-transparent px-2.5 py-3 text-secondary hover:text-paper",
                  exploreActive && "border-accent text-paper",
                )}
                aria-expanded={exploreOpen}
                aria-haspopup="true"
                aria-controls={exploreId}
                onClick={() => setExploreOpen((value) => !value)}
              >
                Explore
              </button>
              {exploreOpen ? (
                <div id={exploreId} className="absolute left-0 z-40 mt-1 min-w-40 rounded-md border border-line bg-elevated p-1">
                  {explore.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      aria-current={active(pathname, link.href) ? "page" : undefined}
                      className={cn(
                        "block rounded-sm px-3 py-2 text-secondary hover:bg-white/5 hover:text-paper",
                        active(pathname, link.href) && "bg-accent/10 text-paper",
                      )}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              ) : null}
            </div>
            {rest.map((link) => (
              <NavLink key={link.href} href={link.href} current={active(pathname, link.href)}>
                {link.label}
              </NavLink>
            ))}
          </nav>
          <button
            type="button"
            className="ml-auto inline-flex min-h-11 min-w-11 items-center justify-center rounded-md border border-line px-3 text-sm md:hidden"
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
              <li>
                <Link
                  href="/studio"
                  aria-current={studioCurrent ? "page" : undefined}
                  className="flex min-h-11 items-center rounded-md bg-amber px-3 text-base font-semibold text-ink"
                >
                  Studio
                </Link>
              </li>
              <li className="px-2 pt-3 text-xs text-secondary">Explore</li>
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
      <main id="content" className="mx-auto min-w-0 w-full max-w-7xl flex-1 px-4 py-6">
        {children}
      </main>
      <footer className="border-t border-line bg-panel">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-6 text-sm sm:flex-row sm:items-center sm:justify-between">
          <p className="text-secondary">
            Built by{" "}
            <a
              href="https://www.linkedin.com/in/himajapaturi/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-paper underline decoration-line underline-offset-4"
            >
              Himaja Paturi
            </a>
          </p>
          <nav aria-label="Footer" className="flex flex-wrap gap-x-4 gap-y-2">
            {footerLinks.map((link) => (
              <Link key={link.href} href={link.href} className="text-secondary hover:text-paper">
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </footer>
    </div>
  );
}

function NavLink({ href, current, children }: { href: string; current: boolean; children: ReactNode }) {
  return (
    <Link
      href={href}
      aria-current={current ? "page" : undefined}
      className={cn(
        "border-b-2 border-transparent px-2.5 py-3 text-secondary hover:text-paper",
        current && "border-accent text-paper",
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
          current ? "bg-accent/15 text-paper" : "text-secondary",
        )}
      >
        {children}
      </Link>
    </li>
  );
}
