$ExtraFiles = "WinSAT.reg", "WinSAT.cmd", "brigadier.cmd", "unattend_capture.xml", "Synchronous-ZipAndUnzip.psm1", "copy-windrivers.ps1"
$Floppy = "A:"
$DriverDestDir = "$Env:windir\inf"
$ExtrasDir = "$Env:SYSTEMDRIVE\Extras"

New-Item -ItemType Directory -Force -Path $ExtrasDir

# Copy the drivers by filtering only driver-related files
# no -Recurse for gci needed because the floppy has no directories, only flat files
#Get-ChildItem "$Floppy\*" -Include @("*.cat","*.inf", "*.man", "*.sys") |
#    % {Copy-Item -Path "$_" -Destination $DriverDestDir}

# Copy extras
$ExtraFiles | Copy-Item -Path {"$Floppy\$_"} -dest $ExtrasDir
