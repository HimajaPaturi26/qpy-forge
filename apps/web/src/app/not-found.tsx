import Link from "next/link";

export default function NotFound() {
  return (
    <div className="space-y-3">
      <p className="text-sm text-amber">404</p>
      <h1 className="text-3xl font-semibold">That page is not in the studio.</h1>
      <p className="text-sm text-muted">The route does not match a Q2Py Studio page.</p>
      <Link href="/" className="inline-block text-sm text-amber">
        Back to the start
      </Link>
    </div>
  );
}
