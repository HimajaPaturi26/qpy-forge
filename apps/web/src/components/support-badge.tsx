import { supportLabel } from "@/lib/format";
import { cn } from "@/lib/cn";

const tones: Record<string, string> = {
  supported: "bg-ok/15 text-ok",
  partial: "bg-warn/15 text-warn",
  unsupported: "bg-bad/15 text-bad",
  "oracle-unavailable": "bg-white/10 text-muted",
};

export function SupportBadge({ support }: { support: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        tones[support] ?? "bg-white/10 text-muted",
      )}
    >
      {supportLabel(support)}
    </span>
  );
}
