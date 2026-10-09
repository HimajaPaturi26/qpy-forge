"use client";

import { useEffect, useState } from "react";
import { JsonBlock } from "@/components/json-block";
import { SupportBadge } from "@/components/support-badge";
import { Notice, PageHeader } from "@/components/ui/notice";
import { api } from "@/lib/api";
import { historyStatusLabel, stageLabel } from "@/lib/format";
import type { HistoryEvent, StatusPayload } from "@/lib/types";

export default function HistoryPage() {
  const [events, setEvents] = useState<HistoryEvent[] | null>(null);
  const [status, setStatus] = useState<StatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<HistoryEvent | null>(null);

  useEffect(() => {
    api<{ events: HistoryEvent[] }>("/api/v1/history")
      .then((payload) => setEvents(payload.events))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Could not load history"));
    api<StatusPayload>("/api/v1/status")
      .then(setStatus)
      .catch(() => setStatus(null));
  }, []);

  async function open(id: number) {
    setError(null);
    try {
      const event = await api<HistoryEvent>(`/api/v1/history/${id}`);
      setSelected(event);
    } catch (err) {
      setSelected(null);
      setError(err instanceof Error ? err.message : "Could not load that event");
    }
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="History"
        lede={
          status
            ? status.persistence.durable
              ? status.persistence.note
              : `Translations and validations are stored in SQLite for this API process. ${status.persistence.note}`
            : "History storage has not been confirmed. The list below is the current history response."
        }
      />
      {error ? <Notice tone="error">{error}</Notice> : null}
      {!events && !error ? <p className="text-sm text-muted">Loading history</p> : null}
      {events && events.length === 0 ? (
        <Notice>No events are stored in this API process. Translate or validate from Studio</Notice>
      ) : null}
      {events && events.length > 0 ? (
        <ul className="divide-y divide-line rounded-md border border-line">
          {events.map((event) => (
            <li key={event.id}>
              <button
                type="button"
                className="w-full px-4 py-3 text-left hover:bg-white/5"
                onClick={() => void open(event.id)}
                aria-current={selected?.id === event.id ? "true" : undefined}
              >
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="font-medium">{event.kind}</span>
                  <SupportBadge support={event.support} />
                  <span className="text-xs text-muted">
                    {event.kind === "translate" ? `Codegen ${stageLabel(event.status).toLowerCase()}` : historyStatusLabel(event.status)}
                  </span>
                  <span className="text-xs text-muted">{event.created_at}</span>
                </div>
                <pre className="mt-2 overflow-auto text-xs text-muted">{event.source}</pre>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {selected?.payload ? (
        <section>
          <h2 className="mb-2 text-sm font-medium">Event {selected.id}</h2>
          <JsonBlock value={selected.payload} />
        </section>
      ) : null}
    </div>
  );
}
