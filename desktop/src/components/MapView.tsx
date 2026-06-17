import { useEffect, useState } from "react";
import { api, type Marker } from "@/lib/api";

const W = 720;
const H = 360;

/** Fully-offline geolocation view: equirectangular HUD plot, no tile server. */
export function MapView() {
  const [markers, setMarkers] = useState<Marker[] | null>(null);

  useEffect(() => {
    api.map().then((d) => setMarkers(d.markers)).catch(() => setMarkers([]));
  }, []);

  if (!markers) return <div className="fui-label p-6 text-accent">// LOADING…</div>;

  const project = (lat: number, lon: number) => ({
    x: ((lon + 180) / 360) * W,
    y: ((90 - lat) / 180) * H,
  });

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="fui-label text-fdim/70">
        // GEO&nbsp;TELEMETRY · {markers.length.toLocaleString("en-US")}&nbsp;FIXES
      </div>
      <div className="relative overflow-hidden border border-border bg-level1/50 backdrop-blur-sm">
        {/* corner brackets */}
        <span className="pointer-events-none absolute left-0 top-0 h-4 w-4 border-l-2 border-t-2 border-accent/70" />
        <span className="pointer-events-none absolute right-0 top-0 h-4 w-4 border-r-2 border-t-2 border-accent/70" />
        <span className="pointer-events-none absolute bottom-0 left-0 h-4 w-4 border-b-2 border-l-2 border-accent/70" />
        <span className="pointer-events-none absolute bottom-0 right-0 h-4 w-4 border-b-2 border-r-2 border-accent/70" />
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
          <rect width={W} height={H} fill="#050B12" />
          {[...Array(11)].map((_, i) => (
            <line key={`v${i}`} x1={(i * W) / 12} y1={0} x2={(i * W) / 12} y2={H}
              stroke="#14304A" strokeWidth={0.5} />
          ))}
          {[...Array(5)].map((_, i) => (
            <line key={`h${i}`} x1={0} y1={((i + 1) * H) / 6} x2={W} y2={((i + 1) * H) / 6}
              stroke="#14304A" strokeWidth={0.5} />
          ))}
          <line x1={0} y1={H / 2} x2={W} y2={H / 2} stroke="#1f7e7c" strokeWidth={0.8} />
          <line x1={W / 2} y1={0} x2={W / 2} y2={H} stroke="#1f7e7c" strokeWidth={0.8} />
          {markers.map((m, i) => {
            const p = project(m.lat, m.lon);
            return (
              <g key={i}>
                <line x1={p.x - 9} y1={p.y} x2={p.x + 9} y2={p.y} stroke="#4FE3E0" strokeWidth={0.6} />
                <line x1={p.x} y1={p.y - 9} x2={p.x} y2={p.y + 9} stroke="#4FE3E0" strokeWidth={0.6} />
                <circle cx={p.x} cy={p.y} r={4} fill="#4FE3E0">
                  <title>{`${m.label} (${m.lat.toFixed(4)}, ${m.lon.toFixed(4)})`}</title>
                </circle>
                <circle cx={p.x} cy={p.y} r={10} fill="none" stroke="#4FE3E0" strokeOpacity={0.4} />
              </g>
            );
          })}
        </svg>
      </div>
      <div className="min-h-0 flex-1 overflow-auto border border-border bg-level1/40 backdrop-blur-sm">
        <table className="w-full text-[12px]">
          <thead className="sticky top-0 bg-level2/90 backdrop-blur">
            <tr>
              <th className="fui-label border-b border-accent/30 px-2.5 py-2.5 text-right text-accent/80">المصدر</th>
              <th className="fui-label border-b border-accent/30 px-2.5 py-2.5 text-right text-accent/80">LAT</th>
              <th className="fui-label border-b border-accent/30 px-2.5 py-2.5 text-right text-accent/80">LON</th>
            </tr>
          </thead>
          <tbody>
            {markers.map((m, i) => (
              <tr key={i} className="border-b border-border/40 hover:bg-accent/5">
                <td className="px-2.5 py-1.5">{m.label}</td>
                <td className="px-2.5 py-1.5 font-mono tabular-nums text-fdim" dir="ltr">{m.lat}</td>
                <td className="px-2.5 py-1.5 font-mono tabular-nums text-fdim" dir="ltr">{m.lon}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
