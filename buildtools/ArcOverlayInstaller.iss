; ArcOverlay Inno Setup Script

[Setup]
AppName=ArcOverlay
AppVersion=1.3.2
DefaultDirName={autopf}\ArcOverlay
DefaultGroupName=ArcOverlay
UninstallDisplayIcon={app}\ArcOverlay.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=ArcOverlay_Installer
SetupIconFile=arcoverlay.ico
WizardStyle=modern

[Files]
; The main executable after PyInstaller build
Source: "dist\ArcOverlay\ArcOverlay.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include all files in the dist directory (onedir build is recommended)
Source: "dist\ArcOverlay\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ArcOverlay"; Filename: "{app}\ArcOverlay.exe"
Name: "{commondesktop}\ArcOverlay"; Filename: "{app}\ArcOverlay.exe"

[Run]
Filename: "{app}\ArcOverlay.exe"; Description: "Launch ArcOverlay"; Flags: nowait postinstall skipifsilent
