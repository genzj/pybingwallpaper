; example2.nsi
;
; This script is based on example1.nsi, but it remember the directory, 
; has uninstall support and (optionally) installs start menu shortcuts.
;
; It will install example2.nsi into a directory that the user selects,

;--------------------------------

;Include Modern UI

  !include "MUI2.nsh"


!define PROGRAM_NAME PyBingWallpaper
; The name of the installer
Name ${PROGRAM_NAME}

; The file to write
OutFile "pybingwp-1-0-0.exe"

; The default installation directory
InstallDir $PROGRAMFILES\Genzj\${PROGRAM_NAME}

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Genzj\${PROGRAM_NAME} "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

; My license
LicenseData LICENSE.txt

;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE "${NSISDIR}\Docs\Modern UI\License.txt"
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"

;--------------------------------
Function upgrade
  Push $R0
; Uninstall old version before install a new one
  ReadRegStr $R0 HKLM \  
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" \
        "UninstallString"
  StrCmp $R0 "" done
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
          "${PROGRAM_NAME} is already installed. $\n$\nClick 'OK' to remove the \
          previous version or 'Cancel' to cancel this upgrade." \
          IDOK uninst  
  Abort

uninst:  
  ReadRegStr $R0 HKLM "Software\Genzj\${PROGRAM_NAME}" "Install_Dir"
  ClearErrors
  Exec $R0\uninstall.exe 
done:
  Pop $R0
FunctionEnd

Function .onInit
  Call upgrade
FunctionEnd


;--------------------------------

; The stuff to install
Section "!PyBingWallpaper Main Programs"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put file there
  !cd ./build/exe.win32-3.3
  File /x *.pyc /x __pycache__ "*"
  !cd ../..
  File "res\bingwallpaper.ico"


  
  ; Write the installation path into the registry
  WriteRegStr HKLM Software\Genzj\${PROGRAM_NAME} "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "DisplayName" ${PROGRAM_NAME}
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"
  
SectionEnd


Section "Start Menu Shortcuts"
  CreateDirectory "$SMPROGRAMS\${PROGRAM_NAME}"
  CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\${PROGRAM_NAME}.lnk" "$INSTDIR\BingWallpaper.exe" "--redownload" "$INSTDIR\bingwallpaper.ico" 0
  CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\${PROGRAM_NAME} Commandline Mode.lnk" "cmd" '/k "$INSTDIR\BingWallpaper-cli.exe" --redownload' \
                 "$INSTDIR\bingwallpaper.ico" 0
SectionEnd

; Create auto startup
Section "Run at Windows Startup"
  CreateShortCut "$SMSTARTUP\${PROGRAM_NAME}.lnk" "$INSTDIR\BingWallpaper.exe" "" "$INSTDIR\bingwallpaper.ico" 0
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}"
  DeleteRegKey HKLM "Software\Genzj\${PROGRAM_NAME}"

  ; Remove files and uninstaller
  Delete "$INSTDIR\*.*"
  Delete "$INSTDIR\__pycache__\*.*"

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\${PROGRAM_NAME}\*.*"
  Delete "$SMSTARTUP\${PROGRAM_NAME}.lnk"

  ; Remove directories used
  RMDir "$SMPROGRAMS\${PROGRAM_NAME}"
  RMDir /r "$INSTDIR"

SectionEnd
