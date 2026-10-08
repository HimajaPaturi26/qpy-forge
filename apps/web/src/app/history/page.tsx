"use client";

import { useEffect, useState } from "react";
import { JsonBlock } from "@/components/json-block";
import { SupportBadge } from "@/components/support-badge";
import { api } from "@/lib/api";
import type { HistoryEvent } from "@/lib/types";

export default function HistoryPage() {
  const [events, setEvents] = useState<HistoryEvent[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<HistoryEvent | null>(null);

  useEffect(() => {
    api<{ events: HistoryEvent[] }>("/api/v1/history")
      .then((payload) => setEvents(payload.events))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load history"));
  }, []);

  async function open(id: number) {
    setError(null);
    try {
      const event = await api<HistoryEvent>(`/api/v1/history/${id}`);
      setSelected(event);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load that event");
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">History</h1>
        <p className="mt-1 text-sm text-muted">Translations and validations stored in the local SQLite database.</p>
      </div>
      {error ? (
        <p className="text-sm text-bad" role="alert">
          {error}
        </p>
      ) : null}
      {!events && !error ? <p className="text-sm text-muted">Loading history…</p> : null}
      {events && events.length === 0 ? (
        <p className="text-sm text-muted">No events yet. Translate or validate something in the studio.</p>
      ) : null}
      {events && events.length > 0 ? (
        <ul className="divide-y divide-line rounded-lg border border-line">
          {events.map((event) => (
            <li key={event.id}>
              <button type="button" className="w-full px-4 py-3 text-left hover:bg-white/5" onClick={() => void open(event.id)}>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-medium">{event.kind}</span>
                  <SupportBadge support={event.support} />
                  <span className="text-xs text-muted">{event.created_at}</span>
                  <span className="text-xs text-muted">{event.status}</span>
                </div>
                <pre className="mt-2 overflow-auto font-mono text-xs text-muted">{event.source}</pre>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {selected?.payload ? (
        <section>
          <h2 className="mb-2 text-sm font-medium text-muted">Event {selected.id}</h2>
          <JsonBlock value={selected.payload} />
        </section>
      ) : null}
    </div>
  );
}
