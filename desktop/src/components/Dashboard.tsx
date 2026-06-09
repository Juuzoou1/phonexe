import { type Overview } from "@/lib/api";
import { StatCard } from "@/components/StatCard";
import { SectionTable } from "@/components/SectionTable";
import { KeywordsView } from "@/components/KeywordsView";
import { AnalyzeBar } from "@/components/AnalyzeBar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export function Dashboard({
  overview,
  onOpenApp,
  onLoaded,
}: {
  overview: Overview | null;
  onOpenApp: (key: string) => void;
  onLoaded: (o: Overview) => void;
}) {
  return (
    <div className="flex h-full flex-col gap-3.5 overflow-auto pl-1">
      <AnalyzeBar onLoaded={onLoaded} />

      {overview && (
        <div className="grid grid-cols-6 gap-3">
          {overview.stats.map((s) => (
            <StatCard key={s.key} k={s.key} value={s.value} />
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3.5">
        <Card className="flex flex-col">
          <CardHeader><CardTitle>التطبيقات</CardTitle></CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-3">
              {(overview?.apps ?? []).map((a) => (
                <button
                  key={a.key}
                  onClick={() => onOpenApp(a.key)}
                  className="flex flex-col items-center gap-2 rounded-card border border-border bg-level2 p-3 transition-colors hover:border-accent"
                >
                  <div className="grid h-12 w-12 place-items-center rounded-[14px] bg-level3 text-[11px] font-bold text-accent">
                    {a.name.slice(0, 2)}
                  </div>
                  <div className="text-[11px]">{a.name}</div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="flex flex-col">
          <CardHeader><CardTitle>الكلمات المفتاحية</CardTitle></CardHeader>
          <CardContent className="min-h-0 flex-1">
            <KeywordsView />
          </CardContent>
        </Card>
      </div>

      <Card className="flex min-h-[260px] flex-col">
        <CardHeader><CardTitle>أحدث الرسائل والمحادثات</CardTitle></CardHeader>
        <CardContent className="min-h-0 flex-1">
          <SectionTable section="sec_messages" />
        </CardContent>
      </Card>
    </div>
  );
}
