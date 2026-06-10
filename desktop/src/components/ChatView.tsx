import { useEffect, useState } from "react";
import { Paperclip, MapPin } from "lucide-react";
import { api, type Conversation } from "@/lib/api";
import { themeFor } from "@/lib/appThemes";

/** App-faithful conversation view: thread list + message bubbles, themed per
 *  app so each messenger reads like its real UI (colors from appThemes.ts). */
export function ChatView({ appKey, appName }: { appKey: string; appName: string }) {
  const [convos, setConvos] = useState<Conversation[] | null>(null);
  const [sel, setSel] = useState(0);
  const th = themeFor(appKey);

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
        <div
          className="flex items-center gap-2 px-3 py-2.5 text-[13px] font-bold text-white"
          style={{ background: th.header }}
        >
          <span className="text-base leading-none opacity-90">{th.glyph}</span>
          {th.name}
        </div>
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
      <div className="flex min-w-0 flex-1 flex-col" style={{ background: th.chatBg }}>
        <div
          className="border-b border-black/30 px-4 py-2.5 text-[13px] font-bold text-white"
          style={{ background: th.header }}
        >
          {active.title} <span className="opacity-70">· {th.name}</span>
        </div>
        <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-4">
          {active.messages.map((m, i) => {
            const mine = m.from_me;
            return (
              <div
                key={i}
                className="flex max-w-[72%] flex-col gap-1 rounded-2xl px-3 py-2 text-[12.5px] shadow-sm"
                style={{
                  alignSelf: mine ? "flex-start" : "flex-end",
                  background: mine ? th.sent : th.recv,
                  color: mine ? th.sentText : th.recvText,
                }}
              >
                {m.text && <span className="whitespace-pre-wrap break-words">{m.text}</span>}
                {m.image && (
                  <span className="flex items-center gap-1 text-[11px] opacity-80">
                    <Paperclip className="h-3.5 w-3.5" /> مرفق وسائط
                  </span>
                )}
                {m.lat != null && m.lon != null && (
                  <span className="flex items-center gap-1 text-[11px] opacity-90">
                    <MapPin className="h-3.5 w-3.5" />
                    {m.lat.toFixed(4)}, {m.lon.toFixed(4)}
                  </span>
                )}
                <span className="text-left text-[10px] opacity-60">
                  {(m.timestamp ?? "").replace("T", " ").slice(0, 19)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
