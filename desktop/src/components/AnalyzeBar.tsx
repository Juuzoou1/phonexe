import { useState } from "react";
import { FolderOpen, Loader2 } from "lucide-react";
import { api, type Overview } from "@/lib/api";

/** Load a backup/extraction folder by path via POST /api/analyze. */
export function AnalyzeBar({ onLoaded }: { onLoaded: (o: Overview) => void }) {
  const [path, setPath] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    if (!path.trim()) return;
    setBusy(true);
    setErr(null);
    try {
      onLoaded(await api.analyze(path.trim()));
    } catch (e) {
      setErr(String(e instanceof Error ? e.message : e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-card border border-border bg-level2 p-3">
      <div className="mb-2 flex items-center gap-2 text-[12px] font-semibold text-fdim">
        <FolderOpen className="h-4 w-4" /> فتح مصدر / نسخة احتياطية
      </div>
      <div className="flex gap-2">
        <input
          value={path}
          onChange={(e) => setPath(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="C:\\path\\to\\Backup\\<udid>  أو مجلد استخراج أندرويد"
          dir="ltr"
          className="flex-1 border border-border bg-level3/70 px-3 py-2 font-mono text-[12.5px] outline-none backdrop-blur-sm focus:border-accent"
        />
        <button
          onClick={run}
          disabled={busy}
          className="flex items-center gap-2 rounded-btn bg-accent px-4 py-2 text-[13px] font-semibold text-level0 transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : null} تحليل
        </button>
      </div>
      {err && <div className="mt-2 text-[11px] text-danger">{err}</div>}
    </div>
  );
}
