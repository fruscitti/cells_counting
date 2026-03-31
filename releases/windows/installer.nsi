; releases/windows/installer.nsi
; NSIS MUI2 installer script for Cell Counter
;
; Wraps the PyInstaller onedir output (releases/dist/CellCounter/) into a
; professional Windows installer wizard with Start Menu shortcut and uninstaller.
;
; Build from the releases/windows/ directory:
;   makensis.exe installer.nsi
; Or from repo root via the GitHub Actions workflow.

!include "MUI2.nsh"
!include "LogicLib.nsh"

; ----- Defines ---------------------------------------------------------------

!define APPNAME     "Cell Counter"
!define APPVERSION  "1.0.0"
!define PUBLISHER   "Cell Counter Lab"
!define INSTALL_DIR "$PROGRAMFILES64\CellCounter"
!define DIST_DIR    "..\..\releases\dist\CellCounter"

; ----- Compression (set before any sections) ---------------------------------

SetCompressor /SOLID lzma

; ----- Installer metadata ----------------------------------------------------

Name            "${APPNAME}"
OutFile         "..\..\releases\CellCounterInstaller.exe"
InstallDir      "${INSTALL_DIR}"
RequestExecutionLevel admin

; ----- MUI Pages (install) ---------------------------------------------------

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; ----- MUI Pages (uninstall) -------------------------------------------------

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; ----- Language --------------------------------------------------------------

!insertmacro MUI_LANGUAGE "English"

; ----- Install section -------------------------------------------------------

Section "Install"

    SetOutPath "$INSTDIR"

    ; Copy entire PyInstaller onedir bundle
    File /r "${DIST_DIR}\*.*"

    ; Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortcut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" \
        "$INSTDIR\CellCounter.exe" "" "$INSTDIR\CellCounter.exe" 0

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    ; Add/Remove Programs registry entries
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "DisplayName" "${APPNAME}"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" \
        "Publisher" "${PUBLISHER}"

SectionEnd

; ----- Uninstall section -----------------------------------------------------

Section "Uninstall"

    ; Remove installation directory
    RMDir /r "$INSTDIR"

    ; Remove Start Menu shortcut and folder
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    RMDir  "$SMPROGRAMS\${APPNAME}"

    ; Remove Add/Remove Programs registry key
    DeleteRegKey HKLM \
        "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

SectionEnd
