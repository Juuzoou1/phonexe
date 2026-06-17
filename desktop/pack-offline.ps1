# Build a portable, OFFLINE phonexe desktop app (Electron UI + bundled engine).
#
# Produces desktop\offline-app\phonexe.exe — a self-contained folder that runs
# with no dev server and no internet: the launcher spawns the bundled Python
# engine (resources\engine\phonexe.exe serve) and loads the built React UI.
#
# Prerequisites (run once, on a machine with internet):
#   1) cd desktop ; npm install          # downloads the Electron binary
#   2) (repo root) pip install pyinstaller ; python build_exe.py   # -> dist\phonexe.exe
#
# Then from desktop\ :  powershell -ExecutionPolicy Bypass -File pack-offline.ps1
#
# This avoids electron-builder (whose winCodeSign step needs symlink privileges
# / Developer Mode on Windows); it assembles the app by hand instead.

$ErrorActionPreference = "Stop"
$d = $PSScriptRoot
$out = Join-Path $d "offline-app"
$engineExe = Join-Path $d "..\dist\phonexe.exe"
$electronDist = Join-Path $d "node_modules\electron\dist"

if (-not (Test-Path (Join-Path $electronDist "electron.exe"))) {
  throw "Electron binary missing. Run 'npm install' in desktop\ first."
}
if (-not (Test-Path $engineExe)) {
  throw "Engine missing ($engineExe). Run 'python build_exe.py' at the repo root first."
}

Write-Host "==> building React UI (vite)…"
& node (Join-Path $d "node_modules\vite\bin\vite.js") build

Write-Host "==> assembling $out …"
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
Copy-Item $electronDist $out -Recurse

$app = Join-Path $out "resources\app"
New-Item -ItemType Directory -Force (Join-Path $app "electron") | Out-Null
Copy-Item (Join-Path $d "electron\main.cjs") (Join-Path $app "electron\main.cjs")
Copy-Item (Join-Path $d "dist") $app -Recurse
Set-Content (Join-Path $app "package.json") -Encoding utf8 `
  -Value '{ "name": "phonexe", "version": "0.1.0", "main": "electron/main.cjs" }'

$eng = Join-Path $out "resources\engine"
New-Item -ItemType Directory -Force $eng | Out-Null
Copy-Item $engineExe (Join-Path $eng "phonexe.exe")

Rename-Item (Join-Path $out "electron.exe") "phonexe.exe"

Write-Host "==> done. Run:  $out\phonexe.exe"
