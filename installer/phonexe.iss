; Inno Setup script for phonexe — builds phonexe-setup.exe (Windows installer).
; The installer is password-protected: the secret install code is 2002.
;
; Build (on Windows, after `python build_exe.py` produces dist\phonexe.exe):
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\phonexe.iss
; Output: installer\Output\phonexe-setup.exe

#define AppName "phonexe"
#define AppVersion "0.1.0"
#define AppPublisher "phonexe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=Output
OutputBaseFilename=phonexe-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Require a secret code to run the installer (encrypted setup).
Password=2002
Encryption=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "..\dist\phonexe.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\phonexe.exe"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\phonexe.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\phonexe.exe"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
