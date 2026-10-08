import { describe, expect, it } from "vitest";
import { formatCount, formatRate, supportLabel } from "./format";

describe("formatRate", () => {
  it("renders a measured proportion to one decimal", () => {
    expect(formatRate(0.9894736842105263)).toBe("98.9%");
    expect(formatRate(1)).toBe("100.0%");
    expect(formatRate(0)).toBe("0.0%");
  });

  it("does not invent a number when the metric is missing", () => {
    expect(formatRate(null)).toBe("—");
    expect(formatRate(undefined)).toBe("—");
    expect(formatCount(null)).toBe("—");
  });

  it("names an unavailable oracle explicitly", () => {
    expect(supportLabel("oracle-unavailable")).toBe("Oracle: unavailable");
  });
});
