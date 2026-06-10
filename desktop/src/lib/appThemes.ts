// Per-app chat palettes mirroring each messenger's real dark-mode UI.
// Kept in sync with the PyQt clone (phonexe/gui/chatview.py APP_THEMES) so the
// React ChatView renders Instagram like Instagram, WhatsApp like WhatsApp, etc.

export interface AppTheme {
  name: string;
  header: string; // header / accent bar color
  sent: string; // outgoing bubble color
  sentText: string;
  recv: string; // incoming bubble color
  recvText: string;
  chatBg: string;
  glyph: string; // small mark shown beside the app name
}

export const APP_THEMES: Record<string, AppTheme> = {
  whatsapp: {
    name: "WhatsApp", header: "#202c33", sent: "#005c4b", sentText: "#e9edef",
    recv: "#202c33", recvText: "#e9edef", chatBg: "#0b141a", glyph: "✆",
  },
  messages: {
    name: "Messages", header: "#1c1c1e", sent: "#0b84ff", sentText: "#ffffff",
    recv: "#26282b", recvText: "#e9e9eb", chatBg: "#000000", glyph: "✉",
  },
  telegram: {
    name: "Telegram", header: "#17212b", sent: "#2b5278", sentText: "#ffffff",
    recv: "#182533", recvText: "#e6ebf5", chatBg: "#0e1621", glyph: "✈",
  },
  instagram: {
    name: "Instagram", header: "#000000", sent: "#3797f0", sentText: "#ffffff",
    recv: "#262626", recvText: "#fafafa", chatBg: "#000000", glyph: "◉",
  },
  discord: {
    name: "Discord", header: "#1e1f22", sent: "#5865f2", sentText: "#ffffff",
    recv: "#2b2d31", recvText: "#dbdee1", chatBg: "#313338", glyph: "✦",
  },
  snapchat: {
    name: "Snapchat", header: "#fffc00", sent: "#0fadff", sentText: "#ffffff",
    recv: "#f0f0f0", recvText: "#111111", chatBg: "#1b1b1b", glyph: "☂",
  },
  signal: {
    name: "Signal", header: "#1b1b1b", sent: "#2c6bed", sentText: "#ffffff",
    recv: "#2a2a2a", recvText: "#e6ebf5", chatBg: "#121212", glyph: "▲",
  },
  messenger: {
    name: "Messenger", header: "#000000", sent: "#0084ff", sentText: "#ffffff",
    recv: "#303030", recvText: "#e6ebf5", chatBg: "#0b0b0b", glyph: "◈",
  },
  tiktok: {
    name: "TikTok", header: "#121212", sent: "#fe2c55", sentText: "#ffffff",
    recv: "#1f1f1f", recvText: "#e6ebf5", chatBg: "#101010", glyph: "♪",
  },
  viber: {
    name: "Viber", header: "#1f1a2e", sent: "#7360f2", sentText: "#ffffff",
    recv: "#2a2440", recvText: "#e9e6f5", chatBg: "#16121f", glyph: "✱",
  },
  line: {
    name: "LINE", header: "#1c1c1c", sent: "#06c755", sentText: "#04331a",
    recv: "#2a2a2a", recvText: "#e9edef", chatBg: "#101010", glyph: "❂",
  },
  kik: {
    name: "Kik", header: "#1f2933", sent: "#82bc23", sentText: "#0b1407",
    recv: "#2b2b2b", recvText: "#e6ebf5", chatBg: "#111417", glyph: "❖",
  },
  wechat: {
    name: "WeChat", header: "#111111", sent: "#07c160", sentText: "#04331a",
    recv: "#2c2c2c", recvText: "#ededed", chatBg: "#101010", glyph: "❀",
  },
  threema: {
    name: "Threema", header: "#0f1b14", sent: "#2c7d40", sentText: "#ffffff",
    recv: "#23282b", recvText: "#e6ebf5", chatBg: "#0c1410", glyph: "◆",
  },
};

const FALLBACK: AppTheme = {
  name: "Chat", header: "#0D1724", sent: "#1d6f70", sentText: "#eafffe",
  recv: "#112132", recvText: "#e6f1ff", chatBg: "#050B12", glyph: "▣",
};

export function themeFor(key: string): AppTheme {
  return APP_THEMES[key] ?? { ...FALLBACK, name: key ? key[0].toUpperCase() + key.slice(1) : "Chat" };
}
