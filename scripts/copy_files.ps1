# This script just copies some files that must be captured in the image so that
# they can be used as part of the oobeSystem phase that is configured upon
# an image restore. You may wish to omit or modify these.
#
# - for example, brigadier.plist can be modified to use a custom CatalogURL
#   key to point brigadier to your own SUS mirror (via Reposado or Apple SUS)

$ExtraFiles = "BootCamp.ps1", "brigadier.plist", "BackToMyMac.cmd", "install-sophos.bat"
$Floppy = "A:"
$DriverDestDir = "$Env:windir\inf"
$ExtrasDir = "$Env:SYSTEMDRIVE\Extras"

New-Item -ItemType Directory -Force -Path $ExtrasDir

# Copy extras
$ExtraFiles | Copy-Item -Path {"$Floppy\$_"} -dest $ExtrasDir

# Stage anything else needed to Extras
# - brigadier
(New-Object System.Net.WebClient).DownloadFile(
  'https://github.com/timsutton/brigadier/releases/download/0.2.4/brigadier.exe',
  "$ExtrasDir\brigadier.exe"
)

(New-Object System.Net.WebClient).DownloadFile(
  'http://path/to/custom/sophos/installer.exe',
  "$ExtrasDir\sophos.exe"
)

# This was an attempt to put driver files directly on the floppy device.
# However, because it's a floppy, it can't be large enough to actually contain
# most or any drivers. The alternate approach would be to host a zip of the
# drivers somewhere that copy_files could download and unzip into the %windir%\inf
# directory. Since we aren't relying on any WinRM provisioning steps we don't
# have the option of sending a driver archive over the wire to the VM.
#
# Copy the drivers by filtering only driver-related files
# no -Recurse for gci needed because the floppy has no directories, only flat files
#Get-ChildItem "$Floppy\*" -Include @("*.cat","*.inf", "*.man", "*.sys") |
#    % {Copy-Item -Path "$_" -Destination $DriverDestDir}
