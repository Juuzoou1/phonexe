import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api, type SectionData } from "@/lib/api";

export function SectionTable({ section }: { section: string }) {
  const [data, setData] = useState<SectionData | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    setData(null);
    const key = section === "sec_overview" ? "sec_messages" : section;
    api.section(key).then(setData).catch(() => setData({ columns: [], rows: [], note: "" }));
  }, [section]);

  if (!data) return <div className="fui-label p-6 text-accent">// LOADING…</div>;

  const rows = q
    ? data.rows.filter((r) => r.some((c) => c.toLowerCase().includes(q.toLowerCase())))
    : data.rows;

  return (
    <div className="flex h-full flex-col">
      {data.note && (
        <div className="mb-2 flex items-start gap-1.5 text-[11px] text-fdim">
          <span className="font-mono text-warn">!</span> {data.note}
        </div>
      )}
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="relative w-60">
          <Search className="absolute right-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-fdim" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="بحث…"
            className="w-full rounded-input border border-border bg-level3/70 py-2 pr-8 pl-3 text-[13px] outline-none backdrop-blur-sm focus:border-accent"
          />
        </div>
        <span className="fui-label text-fdim/60">
          {rows.length.toLocaleString("en-US")} REC
        </span>
      </div>
      <div className="min-h-0 flex-1 overflow-auto rounded-card border border-border bg-level1/40 backdrop-blur-sm">
        <table className="w-full border-collapse text-[12px]">
          <thead className="sticky top-0 z-10 bg-level2/90 backdrop-blur">
            <tr>
              {data.columns.map((c) => (
                <th
                  key={c}
                  className="fui-label border-b border-accent/30 px-2.5 py-2.5 text-right text-accent/80"
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr
                key={i}
                className="border-b border-border/40 odd:bg-level1/30 even:bg-level2/20 hover:bg-accent/5"
              >
                {r.map((cell, j) => (
                  <td
                    key={j}
                    className="max-w-[420px] truncate px-2.5 py-1.5 align-top"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
