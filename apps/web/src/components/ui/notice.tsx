import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Notice({
  tone = "info",
  children,
}: {
  tone?: "info" | "error" | "warn";
  children: ReactNode;
}) {
  return (
    <p
      role={tone === "error" ? "alert" : "status"}
      className={cn(
        "rounded-md border px-3 py-2 text-sm",
        tone === "error" && "border-bad/50 bg-bad/10 text-bad",
        tone === "warn" && "border-warn/40 bg-warn/10 text-paper",
        tone === "info" && "border-line bg-panel text-muted",
      )}
    >
      {children}
    </p>
  );
}

export function PageHeader({
  title,
  lede,
  actions,
}: {
  title: string;
  lede?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {lede ? <p className="mt-1 max-w-3xl text-sm text-muted">{lede}</p> : null}
      </div>
      {actions}
    </div>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="border-t border-line pt-4">
      <h2 className="text-sm font-medium">{title}</h2>
      <div className="mt-2">{children}</div>
    </section>
  );
}

export function MetaRow({ term, children }: { term: string; children: ReactNode }) {
  return (
    <div className="grid gap-0.5 border-b border-line py-2 text-sm last:border-b-0 sm:grid-cols-[11rem_1fr] sm:gap-6">
      <dt className="text-muted">{term}</dt>
      <dd className="min-w-0">{children}</dd>
    </div>
  );
}
