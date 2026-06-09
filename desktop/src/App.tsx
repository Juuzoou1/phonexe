import { useEffect, useState } from "react";
import { api, type Overview } from "@/lib/api";
import { TopBar } from "@/components/TopBar";
import { Sidebar } from "@/components/Sidebar";
import { Dashboard } from "@/components/Dashboard";
import { ChatView } from "@/components/ChatView";
import { MapView } from "@/components/MapView";
import { TimelineView } from "@/components/TimelineView";
import { LinksView } from "@/components/LinksView";
import { IdentitiesView } from "@/components/IdentitiesView";
import { KeywordsView } from "@/components/KeywordsView";
import { ReportsView } from "@/components/ReportsView";
import { SearchView } from "@/components/SearchView";
import { SectionTable } from "@/components/SectionTable";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

const SECTION_TITLES: Record<string, string> = {
  sec_apps: "التطبيقات المثبتة", sec_installed: "جرد التطبيقات",
  sec_messages: "الرسائل والمحادثات", sec_media: "وسائط متعددة",
  sec_calls: "سجل المكالمات", sec_voicemail: "البريد الصوتي",
  sec_contacts: "جهات الاتصال", sec_browser: "سجل التصفح",
  sec_calendar: "التقويم", sec_notes: "الملاحظات", sec_files: "الملفات",
  sec_accounts: "الحسابات", sec_deleted: "البيانات المحذوفة",
  sec_bookmarks: "الإشارات المرجعية", sec_audit: "سجل التدقيق",
};

export default function App() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [view, setView] = useState("sec_overview");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.overview().then(setOverview).catch((e) => setError(String(e)));
  }, []);

  const go = (v: string) => {
    setQuery("");
    setView(v);
  };
  const appName = (key: string) =>
    overview?.apps.find((a) => a.key === key)?.name ?? key;

  const body = () => {
    if (query.trim()) return <SearchView query={query} />;
    if (view === "sec_overview")
      return (
        <Dashboard
          overview={overview}
          onOpenApp={(k) => setView("app:" + k)}
          onLoaded={setOverview}
        />
      );
    if (view === "sec_location") return <MapView />;
    if (view === "sec_timeline") return <TimelineView />;
    if (view === "sec_links") return <LinksView />;
    if (view === "sec_identities") return <IdentitiesView />;
    if (view === "sec_keywords") return <KeywordsView />;
    if (view === "reports") return <ReportsView overview={overview} />;
    if (view.startsWith("app:")) {
      const k = view.slice(4);
      return <ChatView appKey={k} appName={appName(k)} />;
    }
    return (
      <Card className="flex h-full flex-col">
        <CardHeader><CardTitle>{SECTION_TITLES[view] ?? view}</CardTitle></CardHeader>
        <CardContent className="min-h-0 flex-1">
          <SectionTable section={view} />
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="flex h-screen flex-col bg-level0 text-ftext" dir="rtl">
      <TopBar current={view} query={query} onQuery={setQuery} onNav={go} />
      <div className="flex min-h-0 flex-1">
        <Sidebar overview={overview} current={view} onSelect={go} />
        <main className="min-w-0 flex-1 overflow-hidden p-3.5">
          {error ? (
            <Card className="p-6 text-fdim">
              تعذّر الاتصال بمحرّك التحليل. شغّل:{" "}
              <code className="text-accent">python -m phonexe serve</code>
              <div className="mt-2 text-[11px]">{error}</div>
            </Card>
          ) : (
            <div className="h-full">{body()}</div>
          )}
        </main>
      </div>
    </div>
  );
}
