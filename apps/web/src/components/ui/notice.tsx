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
      <div className="max-w-3xl">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {lede ? <div className="mt-2 text-sm leading-6 text-muted">{lede}</div> : null}
      </div>
      {actions}
    </div>
  );
}
