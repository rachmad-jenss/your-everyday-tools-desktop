; --- Before install: kill old processes so files aren't locked ---
!macro preInit
  nsExec::Exec 'taskkill /F /IM YourEverydayTools.exe'
  nsExec::Exec 'taskkill /F /IM "Your Everyday Tools.exe"'
!macroend

; --- On uninstall, kill running processes first, then clean up ---
!macro customUnInstall
  nsExec::ExecToLog 'taskkill /F /IM YourEverydayTools.exe'
  nsExec::ExecToLog 'taskkill /F /IM "Your Everyday Tools.exe"'
  Sleep 1000
  RMDir /r "$INSTDIR\resources\backend\_internal\vendor"
  RMDir /r "$INSTDIR\resources\backend"
!macroend
