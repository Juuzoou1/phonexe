import { useEffect, useState } from "react";
import { api, type LinkRow } from "@/lib/api";

export function LinksView() {
  const [rows, setRows] = useState<LinkRow[] | null>(null);

  useEffect(() => {
    api.links().then((d) => setRows(d.links)).catch(() => setRows([]));
  }, []);

  if (!rows) return <div className="p-6 text-fdim">جارٍ التحميل…</div>;
  const max = rows.reduce((m, r) => Math.max(m, r.interactions), 1);

  return (
    <div className="h-full overflow-auto">
      <div className="mb-3 text-[12px] text-fdim">
        تحليل العلاقات: الأطراف الأكثر تواصلاً مع صاحب الجهاز.
      </div>
      <div className="flex flex-col gap-1.5">
        {rows.map((r, i) => (
          <div key={i} className="flex items-center gap-3 rounded-input bg-level2 px-3 py-2">
            <span className="w-44 truncate text-[13px] font-semibold">{r.counterpart}</span>
            <span className="rounded-input border border-border px-2 py-0.5 text-[10px] text-fdim">
              {r.app}
            </span>
            <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-level3">
              <div
                className="h-full rounded-full bg-accent"
                style={{ width: `${(r.interactions / max) * 100}%` }}
              />
            </div>
            <span className="w-12 text-left text-[12px] font-semibold text-accent">
              {r.interactions.toLocaleString("en-US")}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
