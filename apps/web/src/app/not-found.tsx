import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl space-y-3">
      <p className="text-sm text-amber">404</p>
      <h1 className="text-3xl font-semibold tracking-tight">This page does not exist</h1>
      <p className="text-sm text-muted">The route does not match a Q2Py Forge page</p>
      <Link href="/" className="inline-block rounded-sm text-sm text-amber">
        Back to the start
      </Link>
    </div>
  );
}
