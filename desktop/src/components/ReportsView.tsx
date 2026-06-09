import { useState } from "react";
import { Download, FileJson, FileText } from "lucide-react";
import { api, type Overview } from "@/lib/api";
import { Card } from "@/components/ui/card";

export function ReportsView({ overview }: { overview: Overview | null }) {
  const [busy, setBusy] = useState(false);
  const d = overview?.device ?? {};
  const meta = overview?.meta ?? {};

  const downloadJson = async () => {
    setBusy(true);
    try {
      const report = await api.report();
      const blob = new Blob([JSON.stringify(report, null, 2)], {
        type: "application/json",
      });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "phonexe-report.json";
      a.click();
      URL.revokeObjectURL(a.href);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4 overflow-auto">
      <Card className="p-4">
        <div className="mb-3 text-[15px] font-bold text-accent">ملخّص القضية</div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-[12.5px] xl:grid-cols-3">
          <Field label="الجهاز" value={d.device_name ?? d.model} />
          <Field label="النظام" value={d.product_version ?? d.android_version} />
          <Field label="المنصّة" value={meta.platform} />
          <Field label="الرقم التسلسلي" value={d.serial_number ?? d.serial} />
          <Field label="IMEI" value={d.imei} />
          <Field label="وقت الفحص" value={String(meta.examined_at ?? "").slice(0, 19)} />
        </div>
      </Card>

      <Card className="p-4">
        <div className="mb-3 text-[15px] font-bold text-accent">تصدير التقارير</div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={downloadJson}
            disabled={busy || !overview}
            className="flex items-center gap-2 rounded-btn border border-accent px-4 py-2.5 text-[13px] font-semibold text-accent transition-colors hover:bg-accent hover:text-level0 disabled:opacity-40"
          >
            <FileJson className="h-4 w-4" /> {busy ? "جارٍ…" : "تنزيل JSON"}
          </button>
        </div>
        <div className="mt-3 flex items-start gap-2 text-[11.5px] text-fdim">
          <FileText className="mt-0.5 h-4 w-4 shrink-0" />
          <span>
            تقارير HTML/PDF كاملة تُنشأ من سطر الأوامر:&nbsp;
            <code className="text-accent">phonexe analyze &lt;backup&gt; -o report</code>
            &nbsp;— تُنتج <code>report.json</code> و <code>report.html</code> مع
            هاش سلسلة الحيازة.
          </span>
        </div>
      </Card>

      <div className="flex items-center gap-2 text-[11px] text-fdim">
        <Download className="h-3.5 w-3.5" />
        التنزيل يحفظ نسخة JSON الكاملة المعروضة حالياً من المحرّك المحلي.
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <div className="text-[10px] text-fdim">{label}</div>
      <div className="font-semibold">{value || "—"}</div>
    </div>
  );
}
