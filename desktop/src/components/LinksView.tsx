import { useEffect, useState } from "react";
import { api, type LinkRow } from "@/lib/api";

export function LinksView() {
  const [rows, setRows] = useState<LinkRow[] | null>(null);

  useEffect(() => {
    api.links().then((d) => setRows(d.links)).catch(() => setRows([]));
  }, []);

  if (!rows) return <div className="fui-label p-6 text-accent">// LOADING…</div>;
  const max = rows.reduce((m, r) => Math.max(m, r.interactions), 1);

  return (
    <div className="h-full overflow-auto">
      <div className="fui-label mb-3 text-fdim/70">
        // LINK&nbsp;ANALYSIS · TOP&nbsp;CONTACTS
      </div>
      <div className="flex flex-col">
        {rows.map((r, i) => (
          <div
            key={i}
            className="flex items-center gap-3 border-b border-border/40 px-1 py-2 hover:bg-accent/5"
          >
            <span className="w-44 truncate text-[13px] font-semibold">{r.counterpart}</span>
            <span dir="ltr" className="shrink-0 border border-border px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-fdim">
              {r.app}
            </span>
            <div className="relative h-2 flex-1 overflow-hidden bg-level3">
              <div
                className="h-full bg-accent shadow-glow-cyan"
                style={{ width: `${(r.interactions / max) * 100}%` }}
              />
            </div>
            <span className="w-12 text-left font-mono text-[12px] font-semibold tabular-nums text-accent">
              {r.interactions.toLocaleString("en-US")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
