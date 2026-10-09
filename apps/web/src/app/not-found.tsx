import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl space-y-3">
      <p className="text-sm text-amber">404</p>
      <h1 className="text-xl font-semibold tracking-tight">Not found</h1>
      <p className="text-sm text-muted">No Q2Py Forge route matches this path</p>
      <Link href="/" className="inline-block rounded-sm text-sm text-amber">
        Back to the start
      </Link>
    </div>
  );
}
