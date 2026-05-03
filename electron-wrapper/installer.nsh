; installer.nsh — Custom NSIS hooks for Your Everyday Tools
;
; Electron-builder includes this file twice:
;   1. In the script header  (computeCommonInstallerScriptHeader → scriptGenerator.include)
;   2. Inside the Install Section (installSection.nsh line 1: !include installer.nsh)
;
; The !ifndef guard ensures every definition is processed only once (first = header).

!ifndef YET_INSTALLER_NSH_INCLUDED
!define YET_INSTALLER_NSH_INCLUDED

!include "nsDialogs.nsh"
!include "LogicLib.nsh"

; ── Kill running processes before install / on uninstall ──────────────────────
!macro preInit
  nsExec::Exec 'taskkill /F /IM YourEverydayTools.exe'
  nsExec::Exec 'taskkill /F /IM "Your Everyday Tools.exe"'
!macroend

!macro customUnInstall
  nsExec::ExecToLog 'taskkill /F /IM YourEverydayTools.exe'
  nsExec::ExecToLog 'taskkill /F /IM "Your Everyday Tools.exe"'
  Sleep 1000
  RMDir /r "$INSTDIR\resources\backend\_internal\vendor"
  RMDir /r "$INSTDIR\resources\backend"
!macroend

; ── Variables for component selection ─────────────────────────────────────────
Var /GLOBAL YET_CB_FFmpeg
Var /GLOBAL YET_CB_Tesseract
Var /GLOBAL YET_SEL_FFmpeg      ; 1 = user checked, 0 = unchecked / silent
Var /GLOBAL YET_SEL_Tesseract

; ── Component selection page ──────────────────────────────────────────────────
; Shown after the user picks an install directory ($INSTDIR already set at this point).
Function YET_ComponentsPage
  ; Skip on silent / auto-update installs
  ${If} ${Silent}
    Abort
  ${EndIf}

  nsDialogs::Create 1018
  Pop $0
  ${If} $0 == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 32u \
    "Komponen berikut membutuhkan koneksi internet.$\n\
Bisa dikelola nanti via menu Help -> Kelola Komponen."

  ${NSD_CreateCheckBox} 0 38u 100% 14u \
    "FFmpeg  (~193 MB)  --  Konversi dan trim video/audio, Subtitle, Video ke GIF"
  Pop $YET_CB_FFmpeg
  ${NSD_Check} $YET_CB_FFmpeg

  ${NSD_CreateCheckBox} 0 58u 100% 14u \
    "Tesseract OCR  (~182 MB)  --  OCR PDF dan Gambar ke Teks (Inggris + Indonesia)"
  Pop $YET_CB_Tesseract
  ${NSD_Check} $YET_CB_Tesseract

  ${NSD_CreateLabel} 0 82u 100% 12u \
    "Total jika semua dipilih: ~375 MB. Download berjalan selama proses instalasi."

  nsDialogs::Show
FunctionEnd

Function YET_ComponentsPageLeave
  ${NSD_GetState} $YET_CB_FFmpeg   $YET_SEL_FFmpeg
  ${NSD_GetState} $YET_CB_Tesseract $YET_SEL_Tesseract
FunctionEnd

; Insert page after directory selection, before instfiles
!macro customPageAfterChangeDir
  Page custom YET_ComponentsPage YET_ComponentsPageLeave
!macroend

; ── Download selected components (runs during "Installing..." progress screen) ─
!macro customInstall
  StrCpy $R9 "$INSTDIR\resources\backend\_internal\vendor"

  ; ── FFmpeg ──────────────────────────────────────────────────────────────────
  ${If} $YET_SEL_FFmpeg == 1
    SetDetailsPrint both
    DetailPrint "Mengunduh FFmpeg (~193 MB) ..."

    ExecWait "$\"$SYSDIR\curl.exe$\" --location --silent --show-error \
--output $\"$TEMP\yet-ffmpeg.zip$\" \
https://github.com/rachmad-jenss/your-everyday-tools-desktop/releases/download/components-v1/ffmpeg-windows.zip" $0

    ${If} $0 == 0
      DetailPrint "Mengekstrak FFmpeg ..."
      CreateDirectory "$R9\ffmpeg"
      ExecWait "powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass \
-Command $\"Expand-Archive -LiteralPath '$TEMP\yet-ffmpeg.zip' \
-DestinationPath '$R9\ffmpeg' -Force$\"" $0
      Delete "$TEMP\yet-ffmpeg.zip"
      ${If} $0 != 0
        RMDir /r "$R9\ffmpeg"
        MessageBox MB_OK|MB_ICONEXCLAMATION \
          "Gagal mengekstrak FFmpeg (kode: $0).$\nBisa download ulang nanti lewat Help -> Kelola Komponen."
        StrCpy $YET_SEL_FFmpeg 0
      ${EndIf}
    ${Else}
      Delete "$TEMP\yet-ffmpeg.zip"
      MessageBox MB_OK|MB_ICONEXCLAMATION \
        "Gagal mengunduh FFmpeg (curl: $0).$\nBisa download ulang nanti lewat Help -> Kelola Komponen."
      StrCpy $YET_SEL_FFmpeg 0
    ${EndIf}
  ${EndIf}

  ; ── Tesseract OCR ────────────────────────────────────────────────────────────
  ${If} $YET_SEL_Tesseract == 1
    SetDetailsPrint both
    DetailPrint "Mengunduh Tesseract OCR (~182 MB) ..."

    ExecWait "$\"$SYSDIR\curl.exe$\" --location --silent --show-error \
--output $\"$TEMP\yet-tess.zip$\" \
https://github.com/rachmad-jenss/your-everyday-tools-desktop/releases/download/components-v1/tesseract-windows.zip" $0

    ${If} $0 == 0
      DetailPrint "Mengekstrak Tesseract OCR ..."
      CreateDirectory "$R9\tesseract"
      ExecWait "powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass \
-Command $\"Expand-Archive -LiteralPath '$TEMP\yet-tess.zip' \
-DestinationPath '$R9\tesseract' -Force$\"" $0
      Delete "$TEMP\yet-tess.zip"
      ${If} $0 != 0
        RMDir /r "$R9\tesseract"
        MessageBox MB_OK|MB_ICONEXCLAMATION \
          "Gagal mengekstrak Tesseract OCR (kode: $0).$\nBisa download ulang nanti lewat Help -> Kelola Komponen."
        StrCpy $YET_SEL_Tesseract 0
      ${EndIf}
    ${Else}
      Delete "$TEMP\yet-tess.zip"
      MessageBox MB_OK|MB_ICONEXCLAMATION \
        "Gagal mengunduh Tesseract OCR (curl: $0).$\nBisa download ulang nanti lewat Help -> Kelola Komponen."
      StrCpy $YET_SEL_Tesseract 0
    ${EndIf}
  ${EndIf}

  ; ── Write COMPONENT_FLAG → Electron userData ──────────────────────────────────
  ; Skipped on silent (auto-update) installs to preserve the existing flag.
  ; Electron reads: %APPDATA%\Your Everyday Tools\components-configured.json
  ${IfNot} ${Silent}
    CreateDirectory "$APPDATA\Your Everyday Tools"
    FileOpen $0 "$APPDATA\Your Everyday Tools\components-configured.json" w
    ${If} $YET_SEL_FFmpeg == 1
    ${AndIf} $YET_SEL_Tesseract == 1
      FileWrite $0 '{"ffmpeg":true,"tesseract":true}'
    ${ElseIf} $YET_SEL_FFmpeg == 1
      FileWrite $0 '{"ffmpeg":true,"tesseract":false}'
    ${ElseIf} $YET_SEL_Tesseract == 1
      FileWrite $0 '{"ffmpeg":false,"tesseract":true}'
    ${Else}
      FileWrite $0 '{"skipped":true}'
    ${EndIf}
    FileClose $0
  ${EndIf}

!macroend

!endif ; YET_INSTALLER_NSH_INCLUDED
