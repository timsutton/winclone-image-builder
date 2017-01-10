powershell -Command "(New-Object System.Net.WebClient).DownloadFile('http://www.7-zip.org/a/7z1514-x64.msi', 'C:\Windows\Temp\7zip.msi')"
msiexec /qb /i C:\Windows\Temp\7zip.msi
