import type { OracleStatus } from "@/lib/types";

export function formatRate(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Not measured";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Not measured";
  }
  return String(value);
}

export function supportLabel(support: string): string {
  switch (support) {
    case "supported":
      return "Supported";
    case "partial":
      return "Partial";
    case "unsupported":
      return "Unsupported";
    case "oracle-unavailable":
      return "Oracle unavailable";
    default:
      return support;
  }
}

export function stageLabel(state: string | undefined): string {
  switch (state) {
    case "ok":
      return "Passed";
    case "error":
      return "Failed";
    case "skipped":
      return "Skipped";
    case "partial":
      return "Partial";
    default:
      return "Not run";
  }
}

export function stageTone(state: string | undefined): "ok" | "bad" | "warn" | "muted" {
  switch (state) {
    case "ok":
      return "ok";
    case "error":
      return "bad";
    case "skipped":
    case "partial":
      return "warn";
    default:
      return "muted";
  }
}

export function comparisonLabel(comparison: string): string {
  switch (comparison) {
    case "value-match":
      return "Matched authored value";
    case "value-mismatch":
      return "Authored value mismatch";
    case "signal-match":
      return "Matched authored signal";
    case "signal-mismatch":
      return "Authored signal mismatch";
    case "executed":
      return "Executed, no authored expectation";
    case "runtime-error":
      return "Execution failed";
    case "refused":
      return "Not executed";
    default:
      return comparison;
  }
}

export function oracleSummary(oracle: OracleStatus): { title: string; detail: string } {
  if (!oracle.available) {
    return { title: "Unavailable", detail: oracle.reason };
  }
  return { title: "Not enabled", detail: oracle.reason };
}

export function historyStatusLabel(status: string): string {
  if (status === "ok" || status === "skipped" || status === "error" || status === "partial" || status === "pending") {
    return stageLabel(status);
  }
  return comparisonLabel(status);
}
