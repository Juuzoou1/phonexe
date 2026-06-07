# phonexe — iOS Backup Forensic Analyzer

`phonexe` is a digital-forensics tool that analyzes **iOS device backups** and
produces structured, court-friendly reports (JSON + HTML) of the local
artifacts they contain: contacts, messages, calls, Safari history, photos
(with EXIF/GPS), and chat apps such as WhatsApp, Instagram, Snapchat, Discord,
Telegram and more.

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

| Module        | Source artifact                                  |
|---------------|--------------------------------------------------|
| contacts      | `AddressBook.sqlitedb`                            |
| messages      | `sms.db` (SMS / iMessage)                         |
| calls         | `CallHistory.storedata`                           |
| safari_history| Safari `History.db`                              |
| photos        | Camera Roll media + EXIF/GPS (needs Pillow)      |
| whatsapp      | `ChatStorage.sqlite`                             |
| social_apps   | Instagram, Snapchat, Discord, Telegram, Signal, Messenger, TikTok — auto-detected message-like tables |

Every backup file can also be hashed (MD5/SHA-1/SHA-256) for
**chain-of-custody** verification (`--hash`).

---

## Install & run (from source)

```bash
pip install -r requirements.txt        # Pillow (optional, for EXIF)

# inspect device metadata
python -m phonexe info  /path/to/Backup/<udid>

# full extraction + reports
python -m phonexe analyze /path/to/Backup/<udid> \
    -o report --hash \
    --examiner "Your Name" --case-id "CASE-2026-001"
```

Reports are written to `report/report.json` and `report/report.html`.

### Where are iOS backups?

- **Windows:** `C:\Users\<user>\AppData\Roaming\Apple Computer\MobileSync\Backup\`
- **macOS:** `~/Library/Application Support/MobileSync/Backup/`

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
python tests/make_sample_backup.py sample/backup   # synthetic test backup
python -m pytest                                   # run the test suite
```

The sample backup contains entirely fabricated data and is safe to use for
demos and development.
