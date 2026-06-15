import {
  LayoutDashboard, LayoutGrid, MessageCircle, Image, MapPin, Phone,
  Voicemail, Users, Globe, Calendar, FileText, File, Clock, Share2, Contact,
  KeyRound, Trash2, Bookmark, History, Smartphone, Power,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Overview } from "@/lib/api";

const GROUPS: { cat: string; code: string; items: [string, any, string][] }[] = [
  { cat: "الجهاز", code: "DEVICE", items: [
    ["sec_overview", LayoutDashboard, "نظرة عامة"],
    ["sec_apps", LayoutGrid, "التطبيقات المثبتة"],
    ["sec_installed", LayoutGrid, "جرد التطبيقات"],
  ]},
  { cat: "البيانات المحلّلة", code: "DATA", items: [
    ["sec_messages", MessageCircle, "الرسائل والمحادثات"],
    ["sec_media", Image, "وسائط متعددة"],
    ["sec_location", MapPin, "الموقع الجغرافي"],
    ["sec_calls", Phone, "سجل المكالمات"],
    ["sec_voicemail", Voicemail, "البريد الصوتي"],
    ["sec_contacts", Users, "جهات الاتصال"],
    ["sec_browser", Globe, "سجل التصفح"],
    ["sec_calendar", Calendar, "التقويم"],
    ["sec_notes", FileText, "الملاحظات"],
    ["sec_files", File, "الملفات"],
  ]},
  { cat: "التحليل", code: "ANALYSIS", items: [
    ["sec_timeline", Clock, "الخط الزمني"],
    ["sec_links", Share2, "شبكة العلاقات"],
    ["sec_identities", Contact, "الهويات الموحّدة"],
    ["sec_accounts", KeyRound, "الحسابات"],
    ["sec_deleted", Trash2, "البيانات المحذوفة"],
  ]},
  { cat: "مساحة العمل", code: "WORKSPACE", items: [
    ["sec_bookmarks", Bookmark, "الإشارات المرجعية"],
    ["sec_audit", History, "سجل التدقيق"],
  ]},
];

export function Sidebar({
  overview, current, onSelect,
}: {
  overview: Overview | null;
  current: string;
  onSelect: (k: string) => void;
}) {
  const d = overview?.device ?? {};
  return (
    <aside className="flex w-[280px] shrink-0 flex-col gap-3 border-l border-border bg-level1/55 p-3 backdrop-blur-md">
      <div className="fui-label text-fdim">// CONNECTED&nbsp;DEVICE</div>
      <div className="hud rounded-card border border-hudViolet/40 bg-level2/60 p-3 shadow-glow-violet backdrop-blur-md"
        style={{ ["--hud-accent" as string]: "#A855F7" }}>
        <div className="flex items-center gap-3">
          <Smartphone className="h-9 w-9 text-hudViolet" />
          <div className="min-w-0 flex-1">
            <div className="truncate text-[14px] font-bold">
              {d.device_name ?? d.model ?? "—"}
            </div>
            <div dir="ltr" className="text-right font-mono text-[11px] text-fdim">
              {d.product_version ? `iOS ${d.product_version}` : "—"}
            </div>
            <div className="mt-1 flex items-center gap-1.5 text-[11px] font-semibold text-ok">
              <span className="h-2 w-2 animate-pulse rounded-full bg-ok shadow-[0_0_6px_#21D07A]" />
              <span className="fui-label text-ok">ONLINE</span>
            </div>
          </div>
        </div>
      </div>

      <div className="-mx-1 flex-1 overflow-y-auto px-1">
        {GROUPS.map((g) => (
          <div key={g.cat} className="mb-2">
            <div className="flex items-center gap-1.5 px-1 pb-1 pt-2.5 text-[10px] text-fdim/70">
              <span className="font-mono text-accent2/80">//</span>
              <span className="font-semibold tracking-wide">{g.cat}</span>
              <span className="fui-label ml-auto text-fdim/40">{g.code}</span>
            </div>
            {g.items.map(([key, Icon, label]) => {
              const count = overview?.sections?.[key];
              const active = current === key;
              return (
                <button
                  key={key}
                  onClick={() => onSelect(key)}
                  className={cn(
                    "group flex w-full items-center gap-2.5 rounded-input px-3 py-2 text-[13px] transition-colors",
                    active
                      ? "border-r-2 border-accent bg-accent/10 text-accent shadow-glow-cyan"
                      : "text-fdim hover:bg-level3/70 hover:text-ftext",
                  )}
                >
                  <Icon className="h-[17px] w-[17px]" />
                  <span className="flex-1 text-right">{label}</span>
                  {count ? (
                    <span className={cn(
                      "font-mono text-[11px] tabular-nums",
                      active ? "text-accent" : "text-fdim/70",
                    )}>
                      {count.toLocaleString("en-US")}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      <button className="flex items-center justify-center gap-2 rounded-btn border border-danger/70 py-2.5 text-[13px] font-semibold text-danger transition-colors hover:bg-danger hover:text-ftext">
        <Power className="h-4 w-4" /> إنهاء الفحص
      </button>
    </aside>
  );
}
