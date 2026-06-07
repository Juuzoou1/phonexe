# phonexe — iOS Backup Forensic Analyzer

`phonexe` is a digital-forensics tool that analyzes **iOS and Android** device
data and produces structured, court-friendly reports (JSON + HTML) of the
local artifacts they contain: contacts, messages, calls, browser history,
photos (with EXIF/GPS), and chat apps such as WhatsApp, Instagram, Snapchat,
Discord, Telegram and more.

It is designed to be packaged as a single Windows executable (`phonexe.exe`).

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
