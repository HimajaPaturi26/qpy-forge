"use client";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-bad">500</p>
      <h1 className="text-3xl font-semibold">The page failed while rendering.</h1>
      <p className="text-sm text-muted">{error.message || "Unexpected error."}</p>
      <button type="button" className="rounded-md bg-amber px-3 py-2 text-sm font-medium text-ink" onClick={reset}>
        Try again
      </button>
    </div>
  );
}
