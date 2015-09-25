$ExtrasDir = "$Env:SYSTEMDRIVE\Extras"

$SynchronousZipAndUnzipModulePath = Join-Path $ExtrasDir 'Synchronous-ZipAndUnzip.psm1'
Import-Module -Name $SynchronousZipAndUnzipModulePath

# Testing a copy of drivers located on Tim's Dropbox
# These contain several network drivers pulled from Boot Camp ESDs
# that are needed for newer Macs with Windows 7
$ZipUrl = 'https://dl.dropboxusercontent.com/u/429559/WinDrivers.zip'
$ZipFilePath = Join-Path $ExtrasDir 'WinDrivers.zip'
$p = New-Object System.Net.WebClient
$p.DownloadFile($ZipUrl, $ZipFilePath)

$destinationDirectoryPath = 'c:\windows\inf'
Expand-ZipFile -ZipFilePath $ZipFilePath -DestinationDirectoryPath $destinationDirectoryPath -OverwriteWithoutPrompting
# This sleep may be necessary because Expand-ZipFile does not seem to properly block
# Start-Sleep -s 30
