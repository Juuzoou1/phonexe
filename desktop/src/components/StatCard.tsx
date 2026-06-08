import { Card } from "@/components/ui/card";

const LABELS: Record<string, string> = {
  stat_apps: "التطبيقات",
  stat_messages: "الرسائل",
  stat_photos: "الصور",
  stat_videos: "الفيديوهات",
  stat_files: "الملفات",
  stat_deleted: "المحذوفات",
};

export function StatCard({ k, value }: { k: string; value: number }) {
  return (
    <Card className="bg-level2 px-4 py-3 transition-colors hover:border-accent hover:bg-level3">
      <div className="text-[32px] font-bold leading-none text-accent">
        {value.toLocaleString("en-US")}
      </div>
      <div className="mt-1 text-[12px] text-fdim">{LABELS[k] ?? k}</div>
    </Card>
  );
}
