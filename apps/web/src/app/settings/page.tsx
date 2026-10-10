"use client";

import { useEffect, useState } from "react";
import { MetaRow, Notice, PageHeader, Section } from "@/components/ui/notice";
import { api } from "@/lib/api";
import { oracleSummary } from "@/lib/format";
import type { StatusPayload } from "@/lib/types";

function bytes(value: number): string {
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)} GB`;
  }
  return `${value} bytes`;
}

export default function SettingsPage() {
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<StatusPayload>("/api/v1/status")
      .then(setStatus)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Status request failed"));
  }, []);

  const oracle = status ? oracleSummary(status.oracle) : null;
  const authored = status?.oracle.reason.includes("Authored-value validation still runs") ?? false;

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader title="Status" />
      {!status && !error ? <p className="text-sm text-secondary">Checking API</p> : null}
      {error ? (
        <Notice tone="error">
          {error}. Set Q2PY_API_ORIGIN to the public API URL. Locally the API listens on port 43118.
        </Notice>
      ) : null}
      {status && oracle ? (
        <div className="space-y-6">
          <Section title="Runtime">
            <dl>
              <MetaRow term="API health">Responded</MetaRow>
              <MetaRow term="API version">{status.version}</MetaRow>
            </dl>
          </Section>
          <Section title="Translation and validation">
            <dl>
              <MetaRow term="q oracle">
                {oracle.title}: {oracle.detail}
              </MetaRow>
              {authored ? <MetaRow term="Authored-value validation">Available</MetaRow> : null}
            </dl>
          </Section>
          <Section title="Corpus">
            <dl>
              <MetaRow term="Corpus version">{status.corpus.version}</MetaRow>
              <MetaRow term="Dataset fingerprint">
                <span className="font-mono text-xs">{status.corpus.hash}</span>
              </MetaRow>
              <MetaRow term="Project target">{status.corpus.target}</MetaRow>
              {status.corpus.counts ? (
                <>
                  <MetaRow term="Cases">{status.corpus.counts.all}</MetaRow>
                  <MetaRow term="Holdout">{status.corpus.counts.holdout}</MetaRow>
                  <MetaRow term="Dev">{status.corpus.counts.dev}</MetaRow>
                  <MetaRow term="Coverage">{status.corpus.counts.coverage}</MetaRow>
                </>
              ) : null}
            </dl>
          </Section>
          <Section title="Persistence">
            <dl>
              <MetaRow term="Storage">{status.persistence.engine}</MetaRow>
              <MetaRow term="Durability">{status.persistence.durable ? "Durable" : "Non-durable"}</MetaRow>
              <MetaRow term="Limitation">{status.persistence.note}</MetaRow>
            </dl>
          </Section>
          <Section title="Execution">
            <dl>
              <MetaRow term="User runs">
                {status.sandbox.user_runs} · {status.sandbox.provider}
              </MetaRow>
              <MetaRow term="Isolation">
                {status.sandbox.boundary}
                {status.sandbox.container ? "; container reported" : "; not container-isolated"}
              </MetaRow>
              <MetaRow term="Limits">
                Timeout {status.sandbox.limits.timeout_seconds}s · CPU {status.sandbox.limits.cpu_seconds}s · address
                space {bytes(status.sandbox.limits.address_space_bytes)}
              </MetaRow>
            </dl>
          </Section>
        </div>
      ) : null}
    </div>
  );
}
