import { NextRequest, NextResponse } from "next/server";
import { apiOrigin } from "@/lib/api-origin";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(request: NextRequest, context: RouteContext): Promise<NextResponse> {
  const base = apiOrigin({
    Q2PY_API_ORIGIN: process.env.Q2PY_API_ORIGIN,
    VERCEL: process.env.VERCEL,
  });
  if (!base) {
    return NextResponse.json(
      { detail: "Q2PY_API_ORIGIN is not set to the public API URL." },
      { status: 503 },
    );
  }
  const { path } = await context.params;
  const target = new URL(`${base}/api/${path.join("/")}`);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  const init: RequestInit = { method: request.method, headers, redirect: "manual" };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.text();
  }
  try {
    const response = await fetch(target, init);
    return new NextResponse(await response.arrayBuffer(), {
      status: response.status,
      headers: { "content-type": response.headers.get("content-type") ?? "application/json" },
    });
  } catch {
    return NextResponse.json({ detail: "The translation API is unreachable." }, { status: 502 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
