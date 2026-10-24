; -*- mode: ini -*-
; dsh-pet-chubby_blue_whale onedir installer (Inno Setup 7)
; 自用版安装包脚本，基于上游 packaging/dsh-pet.iss 修改
;
; Compile:
;   "D:\Tool\Inno Setup 7\ISCC.exe" packaging\dsh-pet-chubby_blue_whale.iss
;
; Output: dist-onedir\dsh-pet-chubby_blue_whale-setup.exe

#define MyAppShortName "dsh-pet-chubby_blue_whale"
#define MyAppExeName "dsh-pet-chubby_blue_whale.exe"
#define MyAppDir "..\dist-onedir\dsh-pet-chubby_blue_whale"
#define MyAppId "{{a1b2c3d4-e5f6-7890-abcd-ef1234567890}"
#define MyAppDisplay "dsh-pet-chubby_blue_whale"
#define MyAppVersion "4.4.0"

[Setup]
AppId={#MyAppId}
AppName={#MyAppDisplay}
AppVersion={#MyAppVersion}
AppPublisher=fan-linze
SetupIconFile=..\assets\icon.ico
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#MyAppShortName}
DisableProgramGroupPage=yes
OutputDir=..\dist-onedir
OutputBaseFilename={#MyAppShortName}-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=no
UninstallDisplayName={#MyAppDisplay}

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppShortName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppShortName}}"; Flags: nowait postinstall