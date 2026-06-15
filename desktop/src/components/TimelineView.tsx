import { useEffect, useState } from "react";
import { api, type TimelineEvent } from "@/lib/api";

const TYPE: Record<string, string> = {
  Message: "text-accent border-accent/50",
  Call: "text-ok border-ok/50",
  Web: "text-accent2 border-accent2/50",
  Photo: "text-warn border-warn/50",
};

export function TimelineView() {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null);

  useEffect(() => {
    api.timeline().then((d) => setEvents(d.events)).catch(() => setEvents([]));
  }, []);

  if (!events) return <div className="fui-label p-6 text-accent">// LOADING…</div>;

  return (
    <div className="h-full overflow-auto pr-1">
      <div className="fui-label mb-3 text-fdim/70">
        // EVENT&nbsp;LOG · {events.length.toLocaleString("en-US")}&nbsp;ENTRIES
      </div>
      <div className="flex flex-col">
        {events.map((e, i) => (
          <div
            key={i}
            className="flex items-center gap-3 border-b border-border/40 py-2 hover:bg-accent/5"
          >
            <span className="h-7 w-[3px] shrink-0 bg-accent/50" />
            <span dir="ltr" className="w-[140px] shrink-0 font-mono text-[11px] tabular-nums text-fdim">
              {e.timestamp.replace("T", " ").slice(0, 19)}
            </span>
            <span
              className={`shrink-0 border px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider ${
                TYPE[e.type] ?? "border-border text-fdim"
              }`}
            >
              {e.type}
            </span>
            <span className="w-20 shrink-0 truncate font-mono text-[10px] uppercase text-fdim/55">
              {e.source}
            </span>
            <span className="flex-1 truncate text-[12.5px]">{e.detail}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
