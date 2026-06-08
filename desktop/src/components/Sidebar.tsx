import {
  LayoutDashboard, LayoutGrid, MessageCircle, Image, MapPin, Phone,
  Users, Globe, Calendar, FileText, File, Clock, Share2, Contact,
  KeyRound, Trash2, Bookmark, History, Smartphone, Power,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { Overview } from "@/lib/api";

const GROUPS: { cat: string; items: [string, any, string][] }[] = [
  { cat: "الجهاز", items: [
    ["sec_overview", LayoutDashboard, "نظرة عامة"],
    ["sec_apps", LayoutGrid, "التطبيقات المثبتة"],
    ["sec_installed", LayoutGrid, "جرد التطبيقات"],
  ]},
  { cat: "البيانات المحلّلة", items: [
    ["sec_messages", MessageCircle, "الرسائل والمحادثات"],
    ["sec_media", Image, "وسائط متعددة"],
    ["sec_location", MapPin, "الموقع الجغرافي"],
    ["sec_calls", Phone, "سجل المكالمات"],
    ["sec_contacts", Users, "جهات الاتصال"],
    ["sec_browser", Globe, "سجل التصفح"],
    ["sec_calendar", Calendar, "التقويم"],
    ["sec_notes", FileText, "الملاحظات"],
    ["sec_files", File, "الملفات"],
  ]},
  { cat: "التحليل", items: [
    ["sec_timeline", Clock, "الخط الزمني"],
    ["sec_links", Share2, "شبكة العلاقات"],
    ["sec_identities", Contact, "الهويات الموحّدة"],
    ["sec_accounts", KeyRound, "الحسابات"],
    ["sec_deleted", Trash2, "البيانات المحذوفة"],
  ]},
  { cat: "مساحة العمل", items: [
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
    <aside className="flex w-[280px] shrink-0 flex-col gap-3 border-l border-border bg-level1 p-3">
      <div className="text-[11px] font-semibold text-fdim">الجهاز المتصل</div>
      <div className="rounded-card border border-border bg-level2 p-3">
        <div className="flex items-center gap-3">
          <Smartphone className="h-9 w-9 text-accent" />
          <div className="min-w-0">
            <div className="truncate text-[14px] font-bold">
              {d.device_name ?? d.model ?? "—"}
            </div>
            <div className="text-[11px] text-fdim">
              {d.product_version ? `iOS ${d.product_version}` : ""}
            </div>
            <div className="mt-1 flex items-center gap-1 text-[11px] font-semibold text-ok">
              <span className="h-2 w-2 rounded-full bg-ok" /> تم الاتصال
            </div>
          </div>
        </div>
      </div>

      <div className="-mx-1 flex-1 overflow-y-auto px-1">
        {GROUPS.map((g) => (
          <div key={g.cat} className="mb-2">
            <div className="px-1 pb-1 pt-2 text-[10px] font-bold uppercase tracking-wide text-fdim">
              {g.cat}
            </div>
            {g.items.map(([key, Icon, label]) => {
              const count = overview?.sections?.[key];
              const active = current === key;
              return (
                <button
                  key={key}
                  onClick={() => onSelect(key)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-input px-3 py-2 text-[13px] transition-colors",
                    active
                      ? "bg-level2 text-accent border-r-[3px] border-accent"
                      : "text-fdim hover:bg-level3 hover:text-ftext"
                  )}
                >
                  <Icon className="h-[18px] w-[18px]" />
                  <span className="flex-1 text-right">{label}</span>
                  {count ? (
                    <span className="text-[11px] text-fdim">{count.toLocaleString("en-US")}</span>
                  ) : null}
                </button>
              );
            })}
          </div>
        ))}
      </div>

      <button className="flex items-center justify-center gap-2 rounded-btn border border-danger py-2.5 text-[13px] font-semibold text-danger transition-colors hover:bg-danger hover:text-ftext">
        <Power className="h-4 w-4" /> إنهاء الفحص
      </button>
    </aside>
  );
}
