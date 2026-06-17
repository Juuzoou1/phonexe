# CLAUDE.md — phonexe project context

This file is read automatically by Claude Code. It tells you (the assistant)
everything about this project so you can continue the work on the user's
machine. The user speaks Arabic — reply in Arabic.

## What this project is

**phonexe** is a **digital forensics platform** that analyzes **iOS and
Android** device data (from a backup / filesystem extraction the examiner is
authorized to access) and presents it in a polished desktop UI: contacts,
messages, calls, voicemail, browser history, photos (EXIF/GPS), calendar,
notes, files, installed apps, deleted-record recovery, and chat apps (WhatsApp,
Instagram, Snapchat, Telegram, Discord, Signal, Messenger, TikTok) rendered
like the real apps. Plus timeline, offline map, link analysis, unified
contacts, reports (JSON/HTML/PDF + per-section CSV), multi-device cases, audit
trail, and a case-setup wizard.

## ⚖️ Ethical scope — hard boundaries (do NOT cross)

phonexe analyzes **local artifacts from a lawfully acquired backup/extraction**
only. It must **never**:
- bypass or brute-force passcodes / lock screens,
- defeat encryption, exploit vulnerabilities, or FRP-bypass,
- pull from cloud accounts with stolen credentials.

Encrypted backups are refused by design. Keep all new features within this
authorized-use scope.

## Architecture

- **Python engine** (the core, do not rewrite in JS): `phonexe/`
  - `analyze.py` — auto-detects platform, runs extractors, returns a report dict.
  - `extractors/` (iOS) and `android/` — per-artifact parsers (SQLite/plist).
  - `apps/`, `forensics/sqlite_recover.py` (deleted carving), `backup.py`,
    `timeutil.py`, `hashing.py`, `audit.py`, `ios_acquire.py`.
  - `export.py` — evidence offload: `phonexe export <src> -o <dir>` copies the
    real photos (`media/`) and videos (`videos/`) into separate folders with CSV
    indexes, and renders every conversation to app-themed HTML + `conversations.csv`.
    Photos and videos are **separate artifact categories** (`photos` vs `videos`
    extractors; `sec_media`=الصور, `sec_videos`=الفيديو) so they can be reviewed/
    selected/exported independently.
  - Selection → final report: `export.export_selection` (photos/videos subset,
    used by the API `POST /api/export-selection`) and `export.build_selection_report`
    (combined report from rows the examiner checked across **any** section). In
    the PyQt GUI every tabular section has a leading checkbox column + "أضف
    للتقرير"/"التقرير النهائي" buttons backed by a session cart (`self._cart`).
  - `reporting/` — JSON/HTML/PDF reports.
  - `server.py` + `phonexe serve` — local JSON API for the React frontend.
- **PyQt6 desktop GUI** (current, working): `phonexe/gui/`
  - `mainwindow.py`, `dashboard.py`, `chatview.py`, `instaview.py`,
    `mapview.py`, `datasource.py` (Qt-free data adapter), `theme.py`
    (4-level color tokens), `startup.py` (license + case-setup + neon scan
    page), `widgets.py`, `fluent.py` (PyQt-Fluent-Widgets layer), `anim.py`.
  - Run: `python -m phonexe gui`
- **Electron + React + Tailwind + shadcn frontend** (functional): `desktop/`
  - Consumes the Python API (`phonexe serve`). Run: `cd desktop && npm install
    && npm run dev`. Views: dashboard, app-faithful ChatView, offline MapView,
    Timeline/Links/Identities/Keywords, global search, JSON export.
  - Verify without Electron: `npm run lint` (tsc) + `npm run build` (vite). In
    a shell that can't spawn the npm cmd shim, call the bins via node directly:
    `node node_modules/typescript/bin/tsc --noEmit`,
    `node node_modules/vite/bin/vite.js build`.

## Design system

4-level elevation: `level0 #050B12`, `level1 #08121D`, `level2 #0D1724`,
`level3 #112132`; border `#14304A`; accent `#4FE3E0`; secondary `#24A8FF`.
Font: IBM Plex Sans Arabic (bundled). Icons: Lucide + Simple Icons (SVG, in
`phonexe/gui/assets/`). Cards: 12px radius, 1px border, subtle cyan glow.

## How to run / test / build

```bash
pip install -r requirements.txt        # Pillow, PyQt6, PyQt6-Fluent-Widgets, ...
python -m phonexe gui                   # the desktop GUI
python -m phonexe analyze <backup_dir>  # CLI analysis -> JSON/HTML report
python -m phonexe serve                 # JSON API for the React frontend
QT_QPA_PLATFORM=offscreen python -m pytest -q   # tests (keep them green!)
python build_exe.py                     # build phonexe.exe (PyInstaller, on Windows)
```

Generate the synthetic sample backup used by tests/screenshots:
`python tests/make_sample_backup.py sample/backup`

## Secrets / packaging

- **Install code** (Inno Setup installer) and **activation code** (in-app gate):
  both are `2002`. See `phonexe/gui/license.py` and `installer/phonexe.iss`.
- CI (`.github/workflows/build.yml`) builds `phonexe.exe` + `phonexe-setup.exe`
  on Windows and publishes a GitHub **Release** (tag `v0.1.0`) on tag push or
  manual `workflow_dispatch`.
- **App icon**: `phonexe/gui/assets/appicon.ico` (+ `.png`), generated offline by
  `python -m phonexe.gui.assets.make_icon`. Used by `build_exe.py` (`--icon`),
  the installer (`SetupIconFile`), and the GUI window. Regenerate if the palette
  changes.

## Chat apps coverage

- Detected messengers (iOS `apps/social.py` by domain, Android `android/social.py`
  by package): Instagram, Snapchat, Discord, Telegram, Signal, Messenger, TikTok,
  Viber, LINE, Kik, WeChat, Threema — plus WhatsApp & native Messages.
- Each app DB is also run through the freelist carver (`dbscan.deleted_fragments`
  → `forensics/sqlite_recover`); recovered deleted fragments live under each
  `databases[].deleted`, with a top-level `deleted_count`.
- React `ChatView` themes each app with its real dark-mode palette via
  `desktop/src/lib/appThemes.ts` (kept in sync with `gui/chatview.py` APP_THEMES).

## Conventions

- Work on branch **`claude/nifty-bardeen-Hi7vj`**. Commit + push when a unit of
  work is complete.
- **Tests must stay green** before committing. Add tests for new logic.
- Keep `phonexe/gui/datasource.py` Qt-free (the API server imports it).
- Headless Qt: run with `QT_QPA_PLATFORM=offscreen`; animations are skipped
  when widgets are not visible (don't reintroduce headless crashes).
- Match the comment density / style of surrounding code.

## Pending / ideas (not required)

- React frontend: main views are done (chat clones, map, timeline, links,
  identities, keywords, reports, search). Still nice-to-have: real per-app
  styling parity with the PyQt clones, media serving over the API.
- ~~Bundle adb.exe~~ — done: `phonexe fetch-adb` downloads Google's
  platform-tools into `gui/assets/tools/` (Apache 2.0, git-ignored);
  `build_exe.py` bundles it into the EXE.
- **Hard-constrained (need external resources, can't be done from code alone):**
  - Live iOS acquisition reliability — needs a physical iPhone + Apple USB
    driver on the host; the always-works path stays "open an existing backup".
  - Code-sign the Windows EXE/installer — needs a real Authenticode code-signing
    certificate; CI is wired to publish unsigned artifacts until one is added.

## Quick reality notes

- Live USB device detection needs host drivers (Apple "Apple Devices" for
  iPhone; ADB/platform-tools for Android). The always-works path is **"Open
  source / extraction"** on an existing backup folder.
