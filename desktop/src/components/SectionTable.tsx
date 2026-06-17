import { useEffect, useState } from "react";
import { Search, Download, CheckSquare, Square } from "lucide-react";
import { api, type SectionData } from "@/lib/api";

export function SectionTable({ section }: { section: string }) {
  const [data, setData] = useState<SectionData | null>(null);
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  // Only photos / videos sections are selectable for a focused report.
  const selectable = section === "sec_media" || section === "sec_videos";

  useEffect(() => {
    setData(null);
    setSelected(new Set());
    setMsg("");
    const key = section === "sec_overview" ? "sec_messages" : section;
    api.section(key).then(setData).catch(() => setData({ columns: [], rows: [], note: "" }));
  }, [section]);

  if (!data) return <div className="fui-label p-6 text-accent">// LOADING…</div>;

  const rows = q
    ? data.rows.filter((r) => r.some((c) => c.toLowerCase().includes(q.toLowerCase())))
    : data.rows;

  // The first column ("path") identifies a media row for selective export.
  const idOf = (r: string[]) => r[0];

  const toggle = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const allShownSelected = rows.length > 0 && rows.every((r) => selected.has(idOf(r)));
  const toggleAll = () => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allShownSelected) rows.forEach((r) => next.delete(idOf(r)));
      else rows.forEach((r) => next.add(idOf(r)));
      return next;
    });
  };

  const exportSelected = async () => {
    if (selected.size === 0) return;
    setBusy(true);
    setMsg("");
    try {
      const paths = [...selected];
      const sel =
        section === "sec_media" ? { photos: paths } : { videos: paths };
      const res = await api.exportSelection(sel);
      setMsg(`✓ تم تصدير ${res.photos + res.videos} عنصر إلى: ${res.dest}`);
    } catch (e) {
      setMsg(`✗ فشل التصدير: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  };

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
        <div className="flex items-center gap-3">
          {selectable && selected.size > 0 && (
            <button
              onClick={exportSelected}
              disabled={busy}
              className="flex items-center gap-1.5 rounded-input border border-accent/50 bg-accent/15 px-3 py-2 text-[12px] font-semibold text-accent hover:bg-accent/25 disabled:opacity-50"
            >
              <Download className="h-3.5 w-3.5" />
              {busy ? "جارٍ التصدير…" : `صدّر المحدّد (${selected.size})`}
            </button>
          )}
          <span className="fui-label text-fdim/60">
            {rows.length.toLocaleString("en-US")} REC
          </span>
        </div>
      </div>
      {msg && (
        <div className="mb-2 text-[11px] text-accent">{msg}</div>
      )}
      <div className="min-h-0 flex-1 overflow-auto rounded-card border border-border bg-level1/40 backdrop-blur-sm">
        <table className="w-full border-collapse text-[12px]">
          <thead className="sticky top-0 z-10 bg-level2/90 backdrop-blur">
            <tr>
              {selectable && (
                <th className="w-9 border-b border-accent/30 px-2 py-2.5">
                  <button onClick={toggleAll} className="text-accent/80">
                    {allShownSelected ? (
                      <CheckSquare className="h-4 w-4" />
                    ) : (
                      <Square className="h-4 w-4" />
                    )}
                  </button>
                </th>
              )}
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
            {rows.map((r, i) => {
              const id = idOf(r);
              const checked = selected.has(id);
              return (
                <tr
                  key={i}
                  className={`border-b border-border/40 hover:bg-accent/5 ${
                    checked ? "bg-accent/10" : "odd:bg-level1/30 even:bg-level2/20"
                  }`}
                >
                  {selectable && (
                    <td className="px-2 py-1.5 align-top">
                      <button onClick={() => toggle(id)} className="text-accent/80">
                        {checked ? (
                          <CheckSquare className="h-4 w-4" />
                        ) : (
                          <Square className="h-4 w-4 text-fdim" />
                        )}
                      </button>
                    </td>
                  )}
                  {r.map((cell, j) => (
                    <td
                      key={j}
                      className="max-w-[420px] truncate px-2.5 py-1.5 align-top"
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
