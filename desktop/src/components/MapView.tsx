import { useEffect, useState } from "react";
import { api, type Marker } from "@/lib/api";

const W = 720;
const H = 360;

/** Fully-offline geolocation view: equirectangular plot, no tile server. */
export function MapView() {
  const [markers, setMarkers] = useState<Marker[] | null>(null);

  useEffect(() => {
    api.map().then((d) => setMarkers(d.markers)).catch(() => setMarkers([]));
  }, []);

  if (!markers) return <div className="p-6 text-fdim">جارٍ التحميل…</div>;

  const project = (lat: number, lon: number) => ({
    x: ((lon + 180) / 360) * W,
    y: ((90 - lat) / 180) * H,
  });

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="overflow-hidden rounded-card border border-border bg-level2">
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
          <rect width={W} height={H} fill="#08121D" />
          {/* graticule */}
          {[...Array(11)].map((_, i) => (
            <line key={`v${i}`} x1={(i * W) / 12} y1={0} x2={(i * W) / 12} y2={H}
              stroke="#14304A" strokeWidth={0.5} />
          ))}
          {[...Array(5)].map((_, i) => (
            <line key={`h${i}`} x1={0} y1={((i + 1) * H) / 6} x2={W} y2={((i + 1) * H) / 6}
              stroke="#14304A" strokeWidth={0.5} />
          ))}
          {/* equator + prime meridian */}
          <line x1={0} y1={H / 2} x2={W} y2={H / 2} stroke="#1f7e7c" strokeWidth={0.8} />
          <line x1={W / 2} y1={0} x2={W / 2} y2={H} stroke="#1f7e7c" strokeWidth={0.8} />
          {markers.map((m, i) => {
            const p = project(m.lat, m.lon);
            return (
              <g key={i}>
                <circle cx={p.x} cy={p.y} r={5} fill="#4FE3E0" fillOpacity={0.85}>
                  <title>{`${m.label} (${m.lat.toFixed(4)}, ${m.lon.toFixed(4)})`}</title>
                </circle>
                <circle cx={p.x} cy={p.y} r={11} fill="none" stroke="#4FE3E0"
                  strokeOpacity={0.4} />
              </g>
            );
          })}
        </svg>
      </div>
      <div className="text-[12px] text-fdim">{markers.length} نقطة جغرافية</div>
      <div className="min-h-0 flex-1 overflow-auto rounded-card border border-border">
        <table className="w-full text-[12px]">
          <thead className="sticky top-0 bg-level2 text-fdim">
            <tr>
              <th className="px-2.5 py-2 text-right font-semibold">المصدر</th>
              <th className="px-2.5 py-2 text-right font-semibold">خط العرض</th>
              <th className="px-2.5 py-2 text-right font-semibold">خط الطول</th>
            </tr>
          </thead>
          <tbody>
            {markers.map((m, i) => (
              <tr key={i} className="odd:bg-level1 even:bg-level2/40 hover:bg-level3">
                <td className="border-b border-border/60 px-2.5 py-1.5">{m.label}</td>
                <td className="border-b border-border/60 px-2.5 py-1.5" dir="ltr">{m.lat}</td>
                <td className="border-b border-border/60 px-2.5 py-1.5" dir="ltr">{m.lon}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
