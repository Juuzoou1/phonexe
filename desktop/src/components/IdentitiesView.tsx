import { useEffect, useState } from "react";
import { Contact } from "lucide-react";
import { api, type Identity } from "@/lib/api";
import { Card } from "@/components/ui/card";

export function IdentitiesView() {
  const [ids, setIds] = useState<Identity[] | null>(null);

  useEffect(() => {
    api.identities().then((d) => setIds(d.identities)).catch(() => setIds([]));
  }, []);

  if (!ids) return <div className="fui-label p-6 text-accent">// LOADING…</div>;

  return (
    <div className="h-full overflow-auto">
      <div className="fui-label mb-3 text-fdim/70">
        // UNIFIED&nbsp;IDENTITIES · {ids.length.toLocaleString("en-US")}
      </div>
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
        {ids.map((it, i) => (
          <Card key={i} className="bg-level2/55 p-3" style={{ ["--hud-accent" as string]: "#A855F7" }}>
            <div className="mb-2 flex items-center gap-2">
              <Contact className="h-5 w-5 text-hudViolet" />
              <span className="truncate text-[14px] font-bold">{it.identity}</span>
              <span className="mr-auto font-mono text-[11px] tabular-nums text-hudViolet">
                {it.interactions.toLocaleString("en-US")}
              </span>
            </div>
            {it.phones && (
              <div dir="ltr" className="text-right font-mono text-[11px] text-fdim">{it.phones}</div>
            )}
            <div className="mt-2 flex flex-wrap gap-1">
              {it.apps.split(", ").filter(Boolean).map((a) => (
                <span
                  key={a}
                  dir="ltr"
                  className="border border-hudViolet/40 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-hudViolet"
                >
                  {a}
                </span>
              ))}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
