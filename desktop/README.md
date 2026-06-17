# phonexe desktop — Electron + React + Tailwind + shadcn/ui

A modern desktop frontend for phonexe, built with **Electron + React + Vite +
Tailwind + shadcn-style components**, running on top of the existing **Python
forensic engine** (served as a local JSON API).

## Architecture

```
Electron (main.cjs)
  ├─ spawns the Python engine:  python -m phonexe serve   (localhost:8765)
  └─ loads the React UI (Vite)  →  fetches /api/* from the engine
```

The Python engine (SQLite/plist parsing, extraction, analysis) is unchanged —
the React UI only consumes its JSON output.

## Develop

Requires Node 18+ and Python 3.11+ with phonexe installed (`pip install -r
../requirements.txt`).

```bash
cd desktop
npm install
npm run dev        # starts Vite + Electron (Electron auto-starts the engine)
```

Load data into the engine (POST to the API or via the Python CLI) and the UI
updates. To test the UI against the sample backup:

```bash
# in another terminal, from the repo root:
python -m phonexe serve &
curl -X POST localhost:8765/api/analyze -d '{"path":"sample/backup"}'
```

## Build a Windows app

```bash
# 1) build the Python engine exe (from repo root, on Windows)
python build_exe.py
# 2) build the Electron app (bundles dist/phonexe.exe as a sidecar)
cd desktop && npm run dist
```

## Design system

- 4-level elevation: `level0 #050B12`, `level1 #08121D`, `level2 #0D1724`,
  `level3 #112132`; border `#14304A`; accent `#4FE3E0`.
- Font: IBM Plex Sans Arabic. Icons: lucide-react (SVG).
- Cards: 12px radius, 1px border, subtle cyan glow.
