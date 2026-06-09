import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import { api, type SearchHit } from "@/lib/api";

export function SearchView({ query }: { query: string }) {
  const [hits, setHits] = useState<SearchHit[] | null>(null);

  useEffect(() => {
    let alive = true;
    setHits(null);
    const t = setTimeout(() => {
      api.search(query).then((d) => alive && setHits(d.hits)).catch(() => alive && setHits([]));
    }, 200);
    return () => {
      alive = false;
      clearTimeout(t);
    };
  }, [query]);

  return (
    <div className="h-full overflow-auto">
      <div className="mb-3 flex items-center gap-2 text-[13px] font-semibold">
        <Search className="h-4 w-4 text-accent" />
        نتائج البحث عن «{query}»
        {hits && <span className="text-fdim">· {hits.length}</span>}
      </div>
      {!hits ? (
        <div className="text-fdim">جارٍ البحث…</div>
      ) : hits.length === 0 ? (
        <div className="text-fdim">لا توجد نتائج.</div>
      ) : (
        <div className="flex flex-col gap-1.5">
          {hits.map((h, i) => (
            <div key={i} className="rounded-input border border-border bg-level2 px-3 py-2">
              <span className="ml-2 rounded-input border border-border px-1.5 py-0.5 text-[10px] text-accent">
                {h.section}
              </span>
              <span className="text-[12.5px]">{h.match}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
