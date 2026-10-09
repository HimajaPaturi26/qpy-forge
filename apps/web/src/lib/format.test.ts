import { describe, expect, it } from "vitest";
import {
  comparisonLabel,
  formatCount,
  formatRate,
  historyStatusLabel,
  oracleSummary,
  stageLabel,
  supportLabel,
} from "./format";

describe("formatRate", () => {
  it("renders a measured proportion to one decimal", () => {
    expect(formatRate(0.9894736842105263)).toBe("98.9%");
    expect(formatRate(1)).toBe("100.0%");
    expect(formatRate(0)).toBe("0.0%");
  });

  it("does not invent a number when the metric is missing", () => {
    expect(formatRate(null)).toBe("Not measured");
    expect(formatRate(undefined)).toBe("Not measured");
    expect(formatCount(null)).toBe("Not measured");
  });

  it("names support levels without treating the oracle as a success", () => {
    expect(supportLabel("supported")).toBe("Supported");
    expect(supportLabel("oracle-unavailable")).toBe("Oracle unavailable");
  });

  it("does not label a skipped stage as passed", () => {
    expect(stageLabel("ok")).toBe("Passed");
    expect(stageLabel("skipped")).toBe("Skipped");
    expect(stageLabel("error")).toBe("Failed");
    expect(stageLabel(undefined)).toBe("Not run");
    expect(stageLabel("pending")).toBe("Not run");
  });

  it("keeps a refusal distinct from a failed comparison", () => {
    expect(comparisonLabel("refused")).toMatch(/did not run/i);
    expect(comparisonLabel("value-match")).toBe("Matched the authored value");
    expect(comparisonLabel("executed")).toMatch(/No authored expectation/);
    expect(historyStatusLabel("skipped")).toBe("Skipped");
  });

  it("does not describe a detected q binary as a completed oracle check", () => {
    expect(
      oracleSummary({
        available: true,
        status: "available",
        reason: "q was found. Oracle execution is not enabled in this build.",
      }).title,
    ).toBe("Live q comparison is not enabled");
    expect(
      oracleSummary({
        available: false,
        status: "oracle-unavailable",
        reason: "q binary not found. Authored-value validation still runs.",
      }).title,
    ).toBe("The q oracle is unavailable");
  });
});
