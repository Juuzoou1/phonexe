import { type Overview } from "@/lib/api";
import { Barcode } from "@/components/fui/Barcode";

function Seg({ value, max = 28, color }: { value: number; max?: number; color: string }) {
  return (
    <div className="flex gap-[2px]">
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          className="h-3.5 w-[5px]"
          style={{ background: i < value ? color : "rgba(255,255,255,.07)" }}
        />
      ))}
    </div>
  );
}

function Dat({ k, v }: { k: string; v?: string | number | null }) {
  return (
    <div className="border-r-2 border-hudViolet/30 pr-2">
      <div dir="ltr" className="fui-label text-right text-fdim/55">{k}</div>
      <div dir="ltr" className="truncate text-right font-mono text-[12px] text-ftext">
        {v != null && v !== "" ? String(v) : "—"}
      </div>
    </div>
  );
}

/** DX-76-style "subject dossier" hero for the examined device. */
export function SubjectDossier({ overview }: { overview: Overview | null }) {
  const d = overview?.device ?? {};
  const meta = overview?.meta ?? {};
  const stats = Object.fromEntries((overview?.stats ?? []).map((s) => [s.key, s.value]));
  const msgs = (stats["stat_messages"] as number) ?? 0;
  const apps = (stats["stat_apps"] as number) ?? 0;
  const deleted = (stats["stat_deleted"] as number) ?? 0;
  const risk = Math.max(2, Math.min(28, Math.round(msgs / 1.1 + deleted * 2 + apps)));
  const name = d.device_name ?? d.model ?? "UNKNOWN SUBJECT";
  const serial = d.serial_number ?? d.serial ?? "—";

  return (
    <div className="relative border border-hudViolet/45 bg-level1/55 shadow-glow-violet backdrop-blur-md">
      {/* corner brackets */}
      <span className="pointer-events-none absolute -left-px -top-px h-4 w-4 border-l-2 border-t-2 border-hudViolet" />
      <span className="pointer-events-none absolute -right-px -top-px h-4 w-4 border-r-2 border-t-2 border-hudViolet" />
      <span className="pointer-events-none absolute -bottom-px -left-px h-4 w-4 border-b-2 border-l-2 border-hudViolet" />
      <span className="pointer-events-none absolute -bottom-px -right-px h-4 w-4 border-b-2 border-r-2 border-hudViolet" />

      {/* header strip */}
      <div className="flex items-center justify-between border-b border-hudViolet/25 px-3 py-1.5">
        <span className="fui-label text-hudViolet">// SUBJECT DOSSIER</span>
        <Barcode seed={serial} height={14} className="text-hudViolet/70" />
      </div>

      <div className="flex">
        {/* halftone subject graphic */}
        <div
          className="relative w-44 shrink-0 overflow-hidden border-l border-hudViolet/25"
          style={{ background: "linear-gradient(160deg,#1b0b30,#0a0f18)" }}
        >
          <div className="halftone absolute inset-0 text-hudViolet/45" style={{ ["--ht" as string]: "5px" }} />
          {/* device wireframe + reticle */}
          <svg viewBox="0 0 120 150" className="absolute inset-0 h-full w-full p-4" fill="none"
            stroke="#A855F7" strokeWidth="1.2">
            <rect x="34" y="14" width="52" height="118" rx="7" strokeOpacity="0.85" />
            <line x1="34" y1="28" x2="86" y2="28" strokeOpacity="0.5" />
            <line x1="34" y1="120" x2="86" y2="120" strokeOpacity="0.5" />
            <circle cx="60" cy="126" r="3" strokeOpacity="0.6" />
            {[44, 58, 72, 86, 100].map((y) => (
              <line key={y} x1="40" y1={y} x2="80" y2={y} strokeOpacity="0.25" />
            ))}
            {/* targeting reticle */}
            <circle cx="60" cy="70" r="22" stroke="#18FFC8" strokeOpacity="0.5" strokeDasharray="3 4" />
            <line x1="60" y1="40" x2="60" y2="48" stroke="#18FFC8" strokeOpacity="0.7" />
            <line x1="60" y1="92" x2="60" y2="100" stroke="#18FFC8" strokeOpacity="0.7" />
            <line x1="30" y1="70" x2="38" y2="70" stroke="#18FFC8" strokeOpacity="0.7" />
            <line x1="82" y1="70" x2="90" y2="70" stroke="#18FFC8" strokeOpacity="0.7" />
          </svg>
          <span className="fui-label absolute bottom-1.5 left-1.5 text-hudViolet/70">REPT66</span>
          <span dir="ltr" className="fui-label absolute right-1.5 top-1.5 text-phosphor/70">SCAN&nbsp;OK</span>
        </div>

        {/* data */}
        <div className="min-w-0 flex-1 p-4">
          <div
            className="truncate font-display text-[34px] font-extrabold uppercase leading-none text-ftext [text-shadow:0_0_18px_rgba(168,85,247,.35)]"
            style={{ fontStretch: "75%" }}
          >
            {name}
          </div>
          <div dir="ltr" className="mt-1 font-mono text-[12px] text-hudViolet">
            ID: {serial} · ROLE: SUSPECT DEVICE
          </div>

          <div className="mt-3.5 grid grid-cols-3 gap-x-4 gap-y-2">
            <Dat k="PLATFORM" v={(meta.platform as string)?.toUpperCase?.()} />
            <Dat k="OS" v={d.product_version ? `iOS ${d.product_version}` : d.android_version} />
            <Dat k="IMEI" v={d.imei} />
            <Dat k="SERIAL" v={serial} />
            <Dat k="EXAMINED" v={String(meta.examined_at ?? "").slice(0, 10)} />
            <Dat k="CONDITION" v="ANALYZED" />
          </div>

          <div className="mt-4">
            <div className="mb-1 flex items-center justify-between">
              <span className="fui-label text-fdim/70">RISK&nbsp;INDEX</span>
              <span dir="ltr" className="font-mono text-[11px] tabular-nums text-hudViolet">
                {Math.round((risk / 28) * 100)}% · MAX
              </span>
            </div>
            <Seg value={risk} color="#A855F7" />
          </div>
        </div>
      </div>
    </div>
  );
}
