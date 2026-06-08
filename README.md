# phonexe — Digital Forensics Platform

`phonexe` is a digital-forensics platform that analyzes **iOS and Android**
device data and produces structured, court-friendly reports (JSON / HTML /
PDF) of the local artifacts they contain — with a dark, bilingual desktop UI
that renders each app the way it really looks.

It is designed to be packaged as a single Windows executable (`phonexe.exe`),
built automatically by CI.

### Capabilities at a glance

- **Acquisition:** iOS direct backup (`acquire-ios`, via Apple's own protocol),
  Android live ADB pull, or analyze an existing backup / filesystem extraction.
- **Decoding:** contacts, SMS/iMessage, calls, Safari + Chrome history, photos
  (EXIF/GPS), calendar, notes, file inventory, WhatsApp, and Instagram /
  Snapchat / Telegram / Discord / Signal / Messenger / TikTok.
- **App-faithful views:** click an app to open its real-looking clone
  (WhatsApp wallpaper + chat, Instagram feed + stories + DMs, …) with the
  device's own conversations, inline media preview, and phone/desktop sizing.
- **Analysis:** unified timeline, offline world map of all locations,
  relationship/link analysis, cross-app contact unification, deleted-record
  recovery (SQLite carving), global search, and evidence bookmarks.
- **Case & integrity:** multi-device cases, chain-of-custody hashing, an audit
  trail of every examiner action, and savable case files.

---

## ⚖️ Scope & legal/ethics notice — read first

`phonexe` analyzes **local artifacts inside a backup you already have lawful,
authorized access to** (e.g. a backup created from an unlocked, *trusted*
device, or one you have a warrant / consent to examine).

It **does NOT and will not**:

- bypass or brute-force device passcodes / lock screens,
- defeat or break iOS encryption,
- exploit device vulnerabilities to access a locked phone,
- pull data from remote cloud accounts or hijack app logins.

If a backup is encrypted, you must decrypt it first using a password you are
**lawfully authorized to use** (e.g. via Finder/iTunes). `phonexe` refuses to
run against an encrypted backup.

> Use only on devices and data you are legally authorized to examine. You are
> responsible for complying with the laws and evidence-handling procedures of
> your jurisdiction.

---

## What it extracts

### iOS (from a decrypted backup)

| Module        | Source artifact                                  |
|---------------|--------------------------------------------------|
| contacts      | `AddressBook.sqlitedb`                            |
| messages      | `sms.db` (SMS / iMessage)                         |
| calls         | `CallHistory.storedata`                           |
| safari_history| Safari `History.db`                              |
| photos        | Camera Roll media + EXIF/GPS (needs Pillow)      |
| whatsapp      | `ChatStorage.sqlite`                             |
| social_apps   | Instagram, Snapchat, Discord, Telegram, Signal, Messenger, TikTok — auto-detected message-like tables |

### Android (from a /data extraction or live ADB)

| Module        | Source artifact                                  |
|---------------|--------------------------------------------------|
| contacts      | `contacts2.db` (contacts provider)               |
| messages      | `mmssms.db` (telephony provider)                 |
| calls         | `calls` table (contacts provider)                |
| whatsapp      | `msgstore.db`                                     |
| social_apps   | Instagram, Snapchat, Discord, Telegram, Signal, Messenger, TikTok |

Every evidence file can also be hashed (MD5/SHA-1/SHA-256) for
**chain-of-custody** verification (`--hash`).

---

## Desktop GUI

A dark, bilingual (Arabic RTL / English) dashboard drives the same backend:

```bash
pip install PyQt6
python -m phonexe gui
```

From the GUI you can open an iOS backup, an Android extraction, or a saved
report; browse each section in searchable tables; watch live extraction
progress; and export JSON + HTML reports. The built `phonexe.exe` launches
this GUI when run with no arguments.

Highlights:

- **App-faithful chat viewer** — clicking an app opens it styled like the real
  thing (WhatsApp green, Telegram blue, iMessage, Instagram, …) with sent /
  received bubbles, inline images (click for full-size preview), and tappable
  location bubbles.
- **Stories strip** — Instagram / Snapchat media shown as circular highlights.
- **Offline world map** — geolocation points (photo EXIF GPS + in-chat shared
  locations) plotted on a bundled vector map, no internet required.
- **Timeline** — every dated event (messages, calls, web visits, photos)
  merged into one chronological stream.
- **Deleted-data recovery** — best-effort carving of deleted rows from SQLite
  freeblocks and free pages.

## Install & run (from source)

```bash
pip install -r requirements.txt        # Pillow (EXIF) + PyQt6 (GUI)
```

### iOS — analyze a backup

```bash
python -m phonexe info    /path/to/Backup/<udid>     # device metadata
python -m phonexe analyze /path/to/Backup/<udid> \
    -o report --hash \
    --examiner "Your Name" --case-id "CASE-2026-001"
```

Backup locations:
- **Windows:** `C:\Users\<user>\AppData\Roaming\Apple Computer\MobileSync\Backup\`
- **macOS:** `~/Library/Application Support/MobileSync/Backup/`

### Android — analyze a filesystem extraction

Point it at a directory tree copied from the device's `/data` partition
(obtained from a device you are authorized to examine):

```bash
python -m phonexe android-info /path/to/extraction
python -m phonexe android      /path/to/extraction -o report --hash
```

### Android — live ADB logical acquisition

For a connected device with USB debugging enabled and **authorized** (the
on-device prompt accepted by the owner). Requires `adb` on PATH:

```bash
python -m phonexe android-adb -o report --examiner "Your Name"
```

This pulls contacts, SMS and call log via Android content providers. It does
not root the device or bypass any lock.

Reports are written to `report/report.json` and `report/report.html`.

---

## Windows installer & activation code

CI also builds a password-protected Windows installer
(`installer/Output/phonexe-setup.exe`) via Inno Setup:

- The **installer asks for a secret code** before it will install: `2002`.
- On first launch, the app shows an **activation gate** requiring the same
  code `2002`; once entered it is remembered on that machine.

Build the installer manually on Windows (after `python build_exe.py`):

```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\phonexe.iss
```

## Build the Windows EXE

A PyInstaller binary must be built **on the target OS**, so build the Windows
`.exe` on a Windows machine:

```bat
pip install pyinstaller pillow
python build_exe.py
```

Output: `dist\phonexe.exe`. Then:

```bat
phonexe.exe analyze "C:\path\to\Backup\<udid>" -o report --hash
```

---

## Development

```bash
python tests/make_sample_backup.py  sample/backup   # synthetic iOS backup
python tests/make_sample_android.py sample/android  # synthetic Android dump
python -m pytest                                    # run the test suite
```

The sample backup contains entirely fabricated data and is safe to use for
demos and development.
