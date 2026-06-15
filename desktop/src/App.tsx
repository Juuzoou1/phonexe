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
import { Card } from "@/components/ui/card";
import { SectionHeader } from "@/components/fui/SectionHeader";
import { ParticleField } from "@/components/bg/ParticleField";
import { CrtOverlay } from "@/components/bg/CrtOverlay";
import { SvgFilterDefs } from "@/components/bg/SvgFilterDefs";

const TITLES: Record<string, string> = {
  sec_apps: "التطبيقات المثبتة", sec_installed: "جرد التطبيقات",
  sec_messages: "الرسائل والمحادثات", sec_media: "وسائط متعددة",
  sec_location: "الموقع الجغرافي", sec_calls: "سجل المكالمات",
  sec_voicemail: "البريد الصوتي", sec_contacts: "جهات الاتصال",
  sec_browser: "سجل التصفح", sec_calendar: "التقويم", sec_notes: "الملاحظات",
  sec_files: "الملفات", sec_accounts: "الحسابات", sec_deleted: "البيانات المحذوفة",
  sec_bookmarks: "الإشارات المرجعية", sec_audit: "سجل التدقيق",
  sec_timeline: "الخط الزمني", sec_links: "شبكة العلاقات",
  sec_identities: "الهويات الموحّدة", sec_keywords: "الكلمات المفتاحية",
  reports: "تصدير التقارير",
};

const CODES: Record<string, string> = {
  sec_apps: "APPS", sec_installed: "INSTALLED", sec_messages: "MESSAGES",
  sec_media: "MEDIA", sec_location: "GEO", sec_calls: "CALLS",
  sec_voicemail: "VOICEMAIL", sec_contacts: "CONTACTS", sec_browser: "WEB",
  sec_calendar: "CALENDAR", sec_notes: "NOTES", sec_files: "FILES",
  sec_accounts: "ACCOUNTS", sec_deleted: "DELETED", sec_bookmarks: "BOOKMARKS",
  sec_audit: "AUDIT", sec_timeline: "TIMELINE", sec_links: "LINKS",
  sec_identities: "IDENTITIES", sec_keywords: "KEYWORDS", reports: "REPORTS",
};

export default function App() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [view, setView] = useState("sec_overview");
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.overview().then(setOverview).catch((e) => setError(String(e)));
  }, []);

  const go = (v: string) => { setQuery(""); setView(v); };
  const appName = (key: string) =>
    overview?.apps.find((a) => a.key === key)?.name ?? key;

  const meta = (): { title: string; code: string } | null => {
    if (query.trim() || view === "sec_overview") return null;
    if (view.startsWith("app:")) return { title: appName(view.slice(4)), code: "CHAT" };
    return { title: TITLES[view] ?? view, code: CODES[view] ?? "DATA" };
  };

  const body = () => {
    if (query.trim()) return <SearchView query={query} />;
    if (view === "sec_overview")
      return (
        <Dashboard overview={overview} onOpenApp={(k) => setView("app:" + k)} onLoaded={setOverview} />
      );
    if (view === "sec_location") return <MapView />;
    if (view === "sec_timeline") return <TimelineView />;
    if (view === "sec_links") return <LinksView />;
    if (view === "sec_identities") return <IdentitiesView />;
    if (view === "sec_keywords") return <KeywordsView />;
    if (view === "reports") return <ReportsView overview={overview} />;
    if (view.startsWith("app:")) return <ChatView appKey={view.slice(4)} appName={appName(view.slice(4))} />;
    return (
      <Card className="flex h-full flex-col p-3">
        <SectionTable section={view} />
      </Card>
    );
  };

  const m = meta();

  return (
    <div className="relative min-h-screen">
      <ParticleField />
      <div
        className="relative z-10 flex h-screen flex-col bg-level0/70 text-ftext backdrop-blur-sm"
        dir="rtl"
      >
        <TopBar current={view} query={query} onQuery={setQuery} onNav={go} />
        <div className="flex min-h-0 flex-1">
          <Sidebar overview={overview} current={view} onSelect={go} />
          <main className="min-w-0 flex-1 overflow-hidden p-3.5">
            {error ? (
              <Card className="p-6 text-fdim">
                <span className="fui-label text-danger">// CONNECTION&nbsp;LOST</span>
                <div className="mt-2">
                  تعذّر الاتصال بمحرّك التحليل. شغّل:{" "}
                  <code className="font-mono text-accent">python -m phonexe serve</code>
                </div>
                <div className="mt-2 font-mono text-[11px] text-fdim/60">{error}</div>
              </Card>
            ) : (
              <div className="flex h-full flex-col">
                {m && <SectionHeader title={m.title} code={m.code} />}
                <div className="min-h-0 flex-1">{body()}</div>
              </div>
            )}
          </main>
        </div>
      </div>
      <SvgFilterDefs />
      <CrtOverlay />
    </div>
  );
}
