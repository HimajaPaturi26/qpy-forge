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
      return "Matched the authored value";
    case "value-mismatch":
      return "Did not match the authored value";
    case "signal-match":
      return "Matched the authored signal";
    case "signal-mismatch":
      return "Did not match the authored signal";
    case "executed":
      return "Execution finished. No authored expectation was supplied";
    case "runtime-error":
      return "Execution failed";
    case "refused":
      return "Execution did not run because translation was refused or did not compile";
    default:
      return comparison;
  }
}

export function oracleSummary(oracle: OracleStatus): { title: string; detail: string } {
  if (!oracle.available) {
    return {
      title: "The q oracle is unavailable",
      detail: oracle.reason,
    };
  }
  return {
    title: "Live q comparison is not enabled",
    detail: oracle.reason,
  };
}

export function historyStatusLabel(status: string): string {
  if (status === "ok" || status === "skipped" || status === "error" || status === "partial" || status === "pending") {
    return stageLabel(status);
  }
  return comparisonLabel(status);
}
