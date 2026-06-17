import { useEffect, useState } from "react";
import { api, type TimelineEvent } from "@/lib/api";
import { TerminalText } from "@/components/fui/TerminalText";

const TYPE: Record<string, string> = {
  Message: "text-termGreen",
  Call: "text-phosphor",
  Web: "text-accent2",
  Photo: "text-warn",
};

export function TimelineView() {
  const [events, setEvents] = useState<TimelineEvent[] | null>(null);

  useEffect(() => {
    api.timeline().then((d) => setEvents(d.events)).catch(() => setEvents([]));
  }, []);

  if (!events) return <div className="fui-label p-6 text-termGreen">// LOADING…</div>;

  const dot = "................................";

  return (
    <div className="h-full overflow-auto border border-termGreen/30 bg-[#03100b]/80 p-4 backdrop-blur-sm">
      {/* BIOS boot block */}
      <div className="mb-3 font-mono text-[12px] leading-relaxed text-termGreen [text-shadow:0_0_6px_rgba(33,243,138,.4)]">
        <div>
          <TerminalText text="phonexe bios — forensic event sequencer v0.1.0" />
        </div>
        <div className="text-termGreen/70">&gt; mount /evidence {dot} [ OK ]</div>
        <div className="text-termGreen/70">&gt; decode timeline {dot} [ OK ]</div>
        <div className="text-termGreen/70">
          &gt; {events.length.toLocaleString("en-US")} events indexed
        </div>
      </div>

      <div className="flex flex-col">
        {events.map((e, i) => (
          <div
            key={i}
            className="flex items-center gap-2 border-b border-termGreen/10 py-1.5 hover:bg-termGreen/[0.06]"
          >
            <span className="font-mono text-[11px] text-termGreen/45">&gt;</span>
            <span dir="ltr" className="w-[140px] shrink-0 font-mono text-[11px] tabular-nums text-termGreen/80">
              {e.timestamp.replace("T", " ").slice(0, 19)}
            </span>
            <span
              className={`shrink-0 border border-termGreen/40 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider ${
                TYPE[e.type] ?? "text-termGreen"
              }`}
            >
              {e.type}
            </span>
            <span className="w-20 shrink-0 truncate font-mono text-[10px] uppercase text-termGreen/45">
              {e.source}
            </span>
            <span className="flex-1 truncate text-[12.5px] text-termGreen/90">{e.detail}</span>
          </div>
        ))}
      </div>

      <div className="mt-3 font-mono text-[12px] text-termGreen [text-shadow:0_0_6px_rgba(33,243,138,.4)]">
        &gt; <span className="cursor-blink">█</span>
      </div>
    </div>
  );
}
