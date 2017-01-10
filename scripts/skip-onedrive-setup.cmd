reg load "hku\Default" "C:\Users\Default\NTUSER.DAT"
reg delete HKU\default\software\Microsoft\Windows\CurrentVersion\Run /v OneDriveSetup /f
reg unload "hku\Default"
