import { useEffect, useState } from "react";
import { api, type Overview } from "@/lib/api";
import { TopBar } from "@/components/TopBar";
import { Sidebar } from "@/components/Sidebar";
import { StatCard } from "@/components/StatCard";
import { SectionTable } from "@/components/SectionTable";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const SECTION_TITLES: Record<string, string> = {
  sec_apps: "التطبيقات المثبتة", sec_installed: "جرد التطبيقات",
  sec_messages: "الرسائل والمحادثات", sec_media: "وسائط متعددة",
  sec_location: "الموقع الجغرافي", sec_calls: "سجل المكالمات",
  sec_contacts: "جهات الاتصال", sec_browser: "سجل التصفح",
  sec_calendar: "التقويم", sec_notes: "الملاحظات", sec_files: "الملفات",
  sec_timeline: "الخط الزمني", sec_links: "شبكة العلاقات",
  sec_identities: "الهويات الموحّدة", sec_accounts: "الحسابات",
  sec_deleted: "البيانات المحذوفة", sec_bookmarks: "الإشارات المرجعية",
  sec_audit: "سجل التدقيق",
};

export default function App() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [section, setSection] = useState("sec_overview");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.overview().then(setOverview).catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="flex h-screen flex-col bg-level0 text-ftext" dir="rtl">
      <TopBar />
      <div className="flex min-h-0 flex-1">
        <Sidebar overview={overview} current={section} onSelect={setSection} />

        <main className="min-w-0 flex-1 overflow-auto p-3.5">
          {error && (
            <Card className="p-6 text-fdim">
              تعذّر الاتصال بمحرّك التحليل. شغّل: <code>python -m phonexe serve</code>
              <div className="mt-2 text-[11px]">{error}</div>
            </Card>
          )}

          {/* statistics row */}
          {overview && (
            <Card className="mb-3.5 p-4">
              <CardTitle className="mb-3">نظرة عامة على البيانات المستخرجة</CardTitle>
              <div className="grid grid-cols-6 gap-3">
                {overview.stats.map((s) => (
                  <StatCard key={s.key} k={s.key} value={s.value} />
                ))}
              </div>
            </Card>
          )}

          {section === "sec_overview" ? (
            <div className="grid grid-cols-2 gap-3.5">
              <Card>
                <CardHeader><CardTitle>التطبيقات المثبتة</CardTitle></CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-3">
                    {overview?.apps.map((a) => (
                      <button
                        key={a.key}
                        onClick={() => setSection("sec_messages")}
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
                <CardHeader><CardTitle>الرسائل والمحادثات</CardTitle></CardHeader>
                <CardContent className="min-h-0 flex-1">
                  <SectionTable section="sec_messages" />
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="flex h-[calc(100%-120px)] flex-col">
              <CardHeader><CardTitle>{SECTION_TITLES[section] ?? section}</CardTitle></CardHeader>
              <CardContent className="min-h-0 flex-1">
                <SectionTable section={section} />
              </CardContent>
            </Card>
          )}
        </main>
      </div>
    </div>
  );
}
