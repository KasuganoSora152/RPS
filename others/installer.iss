; RPsoft 安装脚本（Inno Setup 7）
; 用法：ISCC.exe "others\installer.iss"
; 产物：dist\RPsoft-setup-0.1.0-win64.exe

#define MyAppName "RPsoft"
#define MyAppVersion "0.0.0"
#define MyAppPublisher "KasuganoSora152"
#define MyAppURL "https://github.com/KasuganoSora152/RPS"
#define MyAppExeName "RPsoft.exe"

[Setup]
AppId={{F0E1D2C3-B4A5-4678-9ABC-DEF012345678}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; 用户数据保存在 %APPDATA%\RPsoft，卸载时保留、不删除数据
OutputDir=..\dist
OutputBaseFilename=RPS-setup-{#MyAppVersion}-win-amd64
SetupIconFile=RPS_icon_multi.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
LicenseFile=..\LICENSE
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription={#MyAppName} Setup

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\RPsoft.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
