import { useEffect, useState } from "react";
import { Paperclip, MapPin } from "lucide-react";
import { api, type Conversation } from "@/lib/api";

/** App-faithful conversation view: thread list + message bubbles. */
export function ChatView({ appKey, appName }: { appKey: string; appName: string }) {
  const [convos, setConvos] = useState<Conversation[] | null>(null);
  const [sel, setSel] = useState(0);

  useEffect(() => {
    setConvos(null);
    setSel(0);
    api.app(appKey).then((d) => setConvos(d.conversations)).catch(() => setConvos([]));
  }, [appKey]);

  if (!convos) return <div className="p-6 text-fdim">جارٍ التحميل…</div>;
  if (convos.length === 0)
    return <div className="p-6 text-fdim">لا توجد محادثات في {appName}.</div>;

  const active = convos[Math.min(sel, convos.length - 1)];

  return (
    <div className="flex h-full overflow-hidden rounded-card border border-border">
      {/* thread list */}
      <div className="w-64 shrink-0 overflow-y-auto border-l border-border bg-level1">
        {convos.map((c, i) => {
          const last = c.messages[c.messages.length - 1];
          return (
            <button
              key={c.title + i}
              onClick={() => setSel(i)}
              className={`flex w-full flex-col gap-0.5 border-b border-border/60 px-3 py-2.5 text-right transition-colors ${
                i === sel ? "bg-level3" : "hover:bg-level2"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-fdim">{c.messages.length}</span>
                <span className="truncate text-[13px] font-semibold">{c.title}</span>
              </div>
              <span className="truncate text-[11px] text-fdim">
                {last?.text ?? (last?.image ? "📎 مرفق" : "")}
              </span>
            </button>
          );
        })}
      </div>

      {/* messages */}
      <div className="flex min-w-0 flex-1 flex-col bg-level0">
        <div className="border-b border-border bg-level1 px-4 py-2.5 text-[13px] font-bold">
          {active.title} <span className="text-fdim">· {appName}</span>
        </div>
        <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-4">
          {active.messages.map((m, i) => (
            <div
              key={i}
              className={`flex max-w-[72%] flex-col gap-1 rounded-card border px-3 py-2 text-[12.5px] ${
                m.from_me
                  ? "self-start border-accent/40 bg-accent/15"
                  : "self-end border-border bg-level2"
              }`}
            >
              {m.text && <span className="whitespace-pre-wrap break-words">{m.text}</span>}
              {m.image && (
                <span className="flex items-center gap-1 text-[11px] text-accent">
                  <Paperclip className="h-3.5 w-3.5" /> مرفق وسائط
                </span>
              )}
              {m.lat != null && m.lon != null && (
                <span className="flex items-center gap-1 text-[11px] text-warn">
                  <MapPin className="h-3.5 w-3.5" />
                  {m.lat.toFixed(4)}, {m.lon.toFixed(4)}
                </span>
              )}
              <span className="text-left text-[10px] text-fdim">
                {(m.timestamp ?? "").replace("T", " ").slice(0, 19)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
