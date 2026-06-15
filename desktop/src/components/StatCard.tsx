import { Card } from "@/components/ui/card";

const LABELS: Record<string, string> = {
  stat_apps: "التطبيقات",
  stat_messages: "الرسائل",
  stat_photos: "الصور",
  stat_videos: "الفيديوهات",
  stat_files: "الملفات",
  stat_deleted: "المحذوفات",
};

const CODES: Record<string, string> = {
  stat_apps: "APPS",
  stat_messages: "MSG",
  stat_photos: "IMG",
  stat_videos: "VID",
  stat_files: "FILE",
  stat_deleted: "DEL",
};

export function StatCard({ k, value }: { k: string; value: number }) {
  return (
    <Card
      className="relative overflow-hidden bg-level2/55 px-4 py-3 transition-colors hover:border-accent hover:bg-level3/60"
      style={{ ["--hud-accent" as string]: "#4FE3E0" }}
    >
      <div className="absolute left-0 top-0 h-[3px] w-8 bg-accent/70" />
      <div className="font-mono text-[32px] font-bold leading-none tabular-nums text-accent [text-shadow:0_0_14px_rgba(79,227,224,.45)]">
        {value.toLocaleString("en-US")}
      </div>
      <div className="mt-1.5 flex items-center justify-between">
        <div className="text-[12px] text-fdim">{LABELS[k] ?? k}</div>
        <div className="fui-label text-fdim/45">{CODES[k] ?? ""}</div>
      </div>
    </Card>
  );
}
