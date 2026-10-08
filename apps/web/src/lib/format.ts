export function formatRate(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return `${(value * 100).toFixed(1)}%`;
}

export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }
  return String(value);
}

export function supportLabel(support: string): string {
  if (support === "oracle-unavailable") {
    return "Oracle: unavailable";
  }
  return support;
}
