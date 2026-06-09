// Tiny client for the local Python engine API (phonexe serve).

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

export interface ChatMessage {
  from_me: boolean;
  text: string | null;
  timestamp: string | null;
  sender: string | null;
  image: string | null;
  lat: number | null;
  lon: number | null;
}
export interface Conversation { title: string; messages: ChatMessage[] }
export interface TimelineEvent {
  timestamp: string; type: string; source: string; detail: string;
}
export interface LinkRow { counterpart: string; app: string; interactions: number }
export interface Identity {
  identity: string; phones: string; apps: string; interactions: number;
}
export interface Marker { lat: number; lon: number; label: string }
export interface SearchHit { section: string; match: string }

export const api = {
  health: () =>
    get<{ ok: boolean; version: string; has_report: boolean }>("/api/health"),
  overview: () => get<Overview>("/api/overview"),
  report: () => get<Record<string, any>>("/api/report"),
  section: (key: string) =>
    get<SectionData>(`/api/section?key=${encodeURIComponent(key)}`),
  app: (key: string) =>
    get<{ conversations: Conversation[] }>(`/api/app?key=${encodeURIComponent(key)}`),
  timeline: () => get<{ events: TimelineEvent[] }>("/api/timeline"),
  links: () => get<{ links: LinkRow[] }>("/api/links"),
  identities: () => get<{ identities: Identity[] }>("/api/identities"),
  map: () => get<{ markers: Marker[] }>("/api/map"),
  keywords: () => get<{ keywords: [string, number][] }>("/api/keywords"),
  search: (q: string) =>
    get<{ hits: SearchHit[] }>(`/api/search?q=${encodeURIComponent(q)}`),
  analyze: async (path: string): Promise<Overview> => {
    const r = await fetch(BASE + "/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    if (!r.ok) throw new Error((await r.json()).error ?? `analyze: ${r.status}`);
    return r.json();
  },
};
