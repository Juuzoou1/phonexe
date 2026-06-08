// Tiny client for the local Python engine API.

const BASE = "http://127.0.0.1:8765";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

export interface Stat { key: string; value: number }
export interface AppRef { key: string; name: string }
export interface Overview {
  device: Record<string, any>;
  meta: Record<string, any>;
  stats: Stat[];
  sections: Record<string, number>;
  apps: AppRef[];
}
export interface SectionData { columns: string[]; rows: string[][]; note: string }

export const api = {
  health: () => get<{ ok: boolean; version: string; has_report: boolean }>("/api/health"),
  overview: () => get<Overview>("/api/overview"),
  section: (key: string) => get<SectionData>(`/api/section?key=${encodeURIComponent(key)}`),
  app: (key: string) => get<{ conversations: any[] }>(`/api/app?key=${encodeURIComponent(key)}`),
  timeline: () => get<{ events: any[] }>("/api/timeline"),
  links: () => get<{ links: any[] }>("/api/links"),
  identities: () => get<{ identities: any[] }>("/api/identities"),
  keywords: () => get<{ keywords: [string, number][] }>("/api/keywords"),
  analyze: async (path: string) => {
    const r = await fetch(BASE + "/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    return r.json();
  },
};
