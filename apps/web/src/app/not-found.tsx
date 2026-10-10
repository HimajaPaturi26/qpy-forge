import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl space-y-3">
      <p className="text-sm text-amber">404</p>
      <h1 className="text-xl font-bold tracking-tight">Not found</h1>
      <p className="text-sm text-secondary">No Q2Py Forge route matches this path.</p>
      <Link href="/" className="inline-block rounded-sm text-sm font-semibold text-accent hover:text-accent-hover">
        Back to the start
      </Link>
    </div>
  );
}
