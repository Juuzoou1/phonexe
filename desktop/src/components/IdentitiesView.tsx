import { useEffect, useState } from "react";
import { Contact } from "lucide-react";
import { api, type Identity } from "@/lib/api";

export function IdentitiesView() {
  const [ids, setIds] = useState<Identity[] | null>(null);

  useEffect(() => {
    api.identities().then((d) => setIds(d.identities)).catch(() => setIds([]));
  }, []);

  if (!ids) return <div className="p-6 text-fdim">جارٍ التحميل…</div>;

  return (
    <div className="h-full overflow-auto">
      <div className="mb-3 text-[12px] text-fdim">
        دمج الهويات عبر جهات الاتصال والتطبيقات والمكالمات.
      </div>
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
        {ids.map((it, i) => (
          <div key={i} className="rounded-card border border-border bg-level2 p-3">
            <div className="mb-2 flex items-center gap-2">
              <Contact className="h-5 w-5 text-accent" />
              <span className="truncate text-[14px] font-bold">{it.identity}</span>
              <span className="mr-auto text-[11px] text-fdim">{it.interactions}</span>
            </div>
            {it.phones && (
              <div className="text-[11.5px] text-fdim" dir="ltr">{it.phones}</div>
            )}
            <div className="mt-2 flex flex-wrap gap-1">
              {it.apps.split(", ").filter(Boolean).map((a) => (
                <span key={a} className="rounded-input border border-border px-1.5 py-0.5 text-[10px] text-accent">
                  {a}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
