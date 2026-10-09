import { describe, expect, it } from "vitest";
import { apiOrigin } from "./api-origin";

describe("apiOrigin", () => {
  it("uses localhost only off Vercel", () => {
    expect(apiOrigin({})).toBe("http://127.0.0.1:43118");
    expect(apiOrigin({ VERCEL: "1" })).toBeNull();
  });

  it("accepts a public origin and rejects loopback on Vercel", () => {
    expect(apiOrigin({ Q2PY_API_ORIGIN: "https://api.example.com/" })).toBe("https://api.example.com");
    expect(apiOrigin({ VERCEL: "1", Q2PY_API_ORIGIN: "http://127.0.0.1:43118" })).toBeNull();
    expect(apiOrigin({ Q2PY_API_ORIGIN: "ftp://api.example.com" })).toBeNull();
  });
});
