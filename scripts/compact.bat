rem exiting early to speed up iteration while debugging
rem exit

if not exist "C:\Windows\Temp\7z920-x64.msi" (
	powershell -Command "(New-Object System.Net.WebClient).DownloadFile('http://downloads.sourceforge.net/sevenzip/7z920-x64.msi', 'C:\Windows\Temp\7z920-x64.msi')"
)
msiexec /qb /i C:\Windows\Temp\7z920-x64.msi

if not exist "C:\Windows\Temp\ultradefrag.zip" (
	powershell -Command "(New-Object System.Net.WebClient).DownloadFile('http://downloads.sourceforge.net/ultradefrag/ultradefrag-portable-6.1.0.bin.amd64.zip', 'C:\Windows\Temp\ultradefrag.zip')"
)

if not exist "C:\Windows\Temp\ultradefrag-portable-6.1.0.amd64\udefrag.exe" (
	cmd /c ""C:\Program Files\7-Zip\7z.exe" x C:\Windows\Temp\ultradefrag.zip -oC:\Windows\Temp"
)

if not exist "C:\Windows\Temp\SDelete.zip" (
  powershell -Command "(New-Object System.Net.WebClient).DownloadFile('http://download.sysinternals.com/files/SDelete.zip', 'C:\Windows\Temp\SDelete.zip')"
)

if not exist "C:\Windows\Temp\sdelete.exe" (
	cmd /c ""C:\Program Files\7-Zip\7z.exe" x C:\Windows\Temp\SDelete.zip -oC:\Windows\Temp"
)

msiexec /qb /x C:\Windows\Temp\7z920-x64.msi

net stop wuauserv
rmdir /S /Q C:\Windows\SoftwareDistribution\Download
mkdir C:\Windows\SoftwareDistribution\Download
net start wuauserv

cmd /c C:\Windows\Temp\ultradefrag-portable-6.1.0.amd64\udefrag.exe --optimize --repeat C:

cmd /c %SystemRoot%\System32\reg.exe ADD HKCU\Software\Sysinternals\SDelete /v EulaAccepted /t REG_DWORD /d 1 /f
cmd /c C:\Windows\Temp\sdelete.exe -q -z C:
