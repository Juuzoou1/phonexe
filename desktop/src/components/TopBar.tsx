import { useEffect, useState } from "react";
import { LayoutDashboard, Download, Search, FileText, Settings, Shield } from "lucide-react";

const NAV: [string, any, string][] = [
  ["dashboard", LayoutDashboard, "لوحة التحكم"],
  ["extract", Download, "استخراج البيانات"],
  ["analyze", Search, "تحليل الأدلة"],
  ["reports", FileText, "التقارير"],
  ["tools", Settings, "الأدوات"],
];

export function TopBar() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <header className="flex h-[72px] items-center gap-5 border-b border-accent/30 bg-gradient-to-b from-level1 to-level0 px-5">
      <Shield className="h-7 w-7 text-accent" />
      <div className="leading-tight">
        <div className="text-[16px] font-bold">الأدلة والمعلومات الجنائية</div>
        <div className="text-[11px] text-fdim">فحص الأجهزة الإلكترونية · v0.1.0</div>
      </div>
      <nav className="mr-6 flex items-center gap-1">
        {NAV.map(([key, Icon, label], i) => (
          <button
            key={key}
            className={`flex items-center gap-2 rounded-input px-4 py-2.5 text-[13px] transition-colors ${
              i === 0
                ? "bg-level2 text-accent border-b-2 border-accent"
                : "text-fdim hover:bg-level2 hover:text-ftext"
            }`}
          >
            <Icon className="h-[18px] w-[18px]" /> {label}
          </button>
        ))}
      </nav>
      <div className="flex-1" />
      <input
        placeholder="بحث شامل في كل البيانات…"
        className="w-60 rounded-input border border-border bg-level3 px-3 py-2 text-[13px] outline-none focus:border-accent"
      />
      <div className="text-left">
        <div className="text-[15px] font-semibold text-accent">
          {now.toLocaleTimeString("en-GB")}
        </div>
        <div className="text-[11px] text-fdim">{now.toISOString().slice(0, 10)}</div>
      </div>
    </header>
  );
}
