import { useEffect, useState } from "react";
import { api, type TimelineEvent } from "@/lib/api";

const TYPE_COLOR: Record<string, string> = {
  Message: "text-accent border-accent/40",
  Call: "text-ok border-ok/40",
  Web: "text-accent2 border-accent2/40",
  Photo: "text-warn border-warn/40",
};

export function TimelineView() {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null);

  useEffect(() => {
    api.timeline().then((d) => setEvents(d.events)).catch(() => setEvents([]));
  }, []);

  if (!events) return <div className="p-6 text-fdim">جارٍ التحميل…</div>;

  return (
    <div className="h-full overflow-auto pr-2">
      <div className="border-r-2 border-border pr-4">
        {events.map((e, i) => (
          <div key={i} className="relative mb-3 pr-4">
            <span className="absolute right-[-21px] top-1.5 h-2.5 w-2.5 rounded-full bg-accent" />
            <div className="rounded-card border border-border bg-level2 px-3 py-2">
              <div className="mb-1 flex items-center gap-2">
                <span className={`rounded-input border px-2 py-0.5 text-[10px] font-semibold ${TYPE_COLOR[e.type] ?? "text-fdim border-border"}`}>
                  {e.type}
                </span>
                <span className="text-[11px] text-fdim">{e.source}</span>
                <span className="mr-auto text-[11px] text-fdim" dir="ltr">
                  {e.timestamp.replace("T", " ").slice(0, 19)}
                </span>
              </div>
              <div className="text-[12.5px]">{e.detail}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
