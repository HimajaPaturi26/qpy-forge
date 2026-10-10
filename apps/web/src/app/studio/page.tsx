import { Suspense } from "react";
import { StudioApp } from "@/components/studio-app";

export default function StudioPage() {
  return (
    <Suspense fallback={<p className="text-sm text-secondary">Loading studio</p>}>
      <StudioApp />
    </Suspense>
  );
}
