import { supportLabel } from "@/lib/format";
import { cn } from "@/lib/cn";

const tones: Record<string, string> = {
  supported: "border-ok/40 text-ok",
  partial: "border-warn/40 text-warn",
  unsupported: "border-bad/40 text-bad",
  "oracle-unavailable": "border-line text-muted",
};

export function SupportBadge({ support }: { support: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs font-medium",
        tones[support] ?? "border-line text-muted",
      )}
    >
      {supportLabel(support)}
    </span>
  );
}
