import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function KeywordsView() {
  const [kw, setKw] = useState<[string, number][] | null>(null);

  useEffect(() => {
    api.keywords().then((d) => setKw(d.keywords)).catch(() => setKw([]));
  }, []);

  if (!kw) return <div className="p-6 text-fdim">جارٍ التحميل…</div>;
  if (kw.length === 0) return <div className="p-6 text-fdim">لا توجد كلمات كافية.</div>;
  const max = kw.reduce((m, [, c]) => Math.max(m, c), 1);

  return (
    <div className="h-full overflow-auto">
      <div className="mb-3 text-[12px] text-fdim">
        الكلمات الأكثر تكراراً في الرسائل (بعد استبعاد الكلمات الشائعة).
      </div>
      <div className="flex flex-col gap-1.5">
        {kw.map(([word, count]) => (
          <div key={word} className="flex items-center gap-3 rounded-input bg-level2 px-3 py-2">
            <span className="w-40 truncate text-[13px] font-semibold">{word}</span>
            <div className="relative h-2.5 flex-1 overflow-hidden rounded-full bg-level3">
              <div className="h-full rounded-full bg-accent2"
                style={{ width: `${(count / max) * 100}%` }} />
            </div>
            <span className="w-10 text-left text-[12px] font-semibold text-accent2">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
