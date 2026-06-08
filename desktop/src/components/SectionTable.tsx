import { useEffect, useState } from "react";
import { api, type SectionData } from "@/lib/api";

export function SectionTable({ section }: { section: string }) {
  const [data, setData] = useState<SectionData | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    setData(null);
    const key = section === "sec_overview" ? "sec_messages" : section;
    api.section(key).then(setData).catch(() => setData({ columns: [], rows: [], note: "" }));
  }, [section]);

  if (!data) return <div className="p-6 text-fdim">جارٍ التحميل…</div>;

  const rows = q
    ? data.rows.filter((r) => r.some((c) => c.toLowerCase().includes(q.toLowerCase())))
    : data.rows;

  return (
    <div className="flex h-full flex-col">
      {data.note && <div className="mb-2 text-[11px] text-fdim">{data.note}</div>}
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="بحث…"
        className="mb-3 w-60 rounded-input border border-border bg-level3 px-3 py-2 text-[13px] outline-none focus:border-accent"
      />
      <div className="min-h-0 flex-1 overflow-auto rounded-card border border-border">
        <table className="w-full border-collapse text-[12px]">
          <thead className="sticky top-0 bg-level2 text-fdim">
            <tr>
              {data.columns.map((c) => (
                <th key={c} className="border-b border-border px-2.5 py-2 text-right font-semibold">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="odd:bg-level1 even:bg-level2/40 hover:bg-level3">
                {r.map((cell, j) => (
                  <td key={j} className="max-w-[420px] truncate border-b border-border/60 px-2.5 py-1.5">
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
