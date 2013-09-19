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
LicenseData $(license)
;--------------------------------
;Interface Settings

  !define MUI_ABORTWARNING

;--------------------------------
;Language Selection Dialog Settings

  ;Remember the installer language
  !define MUI_LANGDLL_REGISTRY_ROOT "HKCU" 
  !define MUI_LANGDLL_REGISTRY_KEY "Software\Genzj" 
  !define MUI_LANGDLL_REGISTRY_VALUENAME "Installer Language"

;--------------------------------
;Pages

  !insertmacro MUI_PAGE_LICENSE $(license)
  !insertmacro MUI_PAGE_COMPONENTS
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
  
;--------------------------------
;Languages
 
  !insertmacro MUI_LANGUAGE "English"
  !insertmacro MUI_LANGUAGE "SimpChinese"


LicenseLangString license ${LANG_ENGLISH} LICENSE.txt
LicenseLangString license ${LANG_SimpChinese} LICENSE-zhcn.txt

;--------------------------------
;Reserve Files
  
  ;If you are using solid compression, files that are required before
  ;the actual installation should be stored first in the data block,
  ;because this will make your installer start faster.
  
  !insertmacro MUI_RESERVEFILE_LANGDLL


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
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd


;--------------------------------

; The stuff to install
Section "!PyBingWallpaper Main Programs" SecMain

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


Section "Start Menu Shortcuts" SecStartMenu
  CreateDirectory "$SMPROGRAMS\${PROGRAM_NAME}"
  CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\${PROGRAM_NAME}.lnk" "$INSTDIR\BingWallpaper.exe" "--redownload" "$INSTDIR\bingwallpaper.ico" 0
  CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\${PROGRAM_NAME} Commandline Mode.lnk" "cmd" '/k "$INSTDIR\BingWallpaper-cli.exe" --redownload' \
                 "$INSTDIR\bingwallpaper.ico" 0
SectionEnd

; Create auto startup
Section "Run at Windows Startup" SecStartup
  CreateShortCut "$SMSTARTUP\${PROGRAM_NAME}.lnk" "$INSTDIR\BingWallpaper.exe" "" "$INSTDIR\bingwallpaper.ico" 0
SectionEnd

;--------------------------------
;Descriptions

  ;USE A LANGUAGE STRING IF YOU WANT YOUR DESCRIPTIONS TO BE LANGAUGE SPECIFIC
  LangString DESC_SecMain_Eng ${LANG_ENGLISH} "Main program files of ${PROGRAM_NAME}."
  LangString DESC_SecStartMenu_Eng ${LANG_ENGLISH} "Create Start Menu shortcuts for ${PROGRAM_NAME}"
  LangString DESC_SecStartup_Eng ${LANG_ENGLISH} "Auto run ${PROGRAM_NAME} at Windows startup (network connection at startup is required)"
  
  LangString DESC_SecMain_Eng ${LANG_SimpChinese} "${PROGRAM_NAME}主程序文件"
  LangString DESC_SecStartMenu_Eng ${LANG_SimpChinese} "在开始菜单创建${PROGRAM_NAME}快捷方式"
  LangString DESC_SecStartup_Eng ${LANG_SimpChinese} "启动Windows时自动运行${PROGRAM_NAME}（启动时需要访问网络）"

  ;Assign descriptions to sections
  !insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain_Eng)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu_Eng)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartup} $(DESC_SecStartup_Eng)
  !insertmacro MUI_FUNCTION_DESCRIPTION_END


;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PROGRAM_NAME}"
  DeleteRegKey HKLM "Software\Genzj\${PROGRAM_NAME}"
  DeleteRegKey /ifempty HKLM "Software\Genzj"

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
