# Steps to build this custom Office installer from scratch:
# Followed https://4sysops.com/archives/office-2016-installation-customize-and-deploy/
# - Download the right arch (x86 in this case) of the Office customization tool here:
#   https://www.microsoft.com/en-us/download/confirmation.aspx?id=49030&6B49FDFB-8E5B-4B07-BC31-15695C5A2143=1
# - Run the customization tool setup, which should create an "admin" folder
# - Mount the Office 2016 VL installer (can be found on maintenance$) and copy the contents out to a new folder
# - Copy the contents of the "admin" folder into the same folder you copied the Office contents into, overwriting
#   any matching files.
# - Open the office2016-lab.msp file with the customization tool to make changes to the existing one, or create
#   a new one. 'office2016-lab.msp' is just the name I chose for our lab Office package. You'll need to specify
#   the exact name in the last of this script where setup.exe is invoked.
# - Test the install in a snapshotted VM using "cmd /c setup.exe /adminfile <msp file>"
# - Use ISO recorder (http://isorecorder.alexfeinman.com/W7.htm) to convert the Office setup + admin + msp file
#   to an ISO, upload it to where this script can pull it down

# This Office 2016 ISO is hosted on an internal website.
# - Why we download from the VM rather than some other method:
#   - WinRM may be a possibility but it can have issues with large files and we currently get away
#     with not enabling WinRM at all
#   - Packer has a webserver for feeding preseed/kickstarter files but we'd still need a way to template
#     in the server IP to this download script. pre-processing this with some built-in webserver and
#     a templating preprocessor like inductor (https://github.com/joefitzgerald/inductor) would probably
#     be the best solution.
# - even better would be if we could pull down the Office ISO from a public MS location and then
#   add our customized MSP via Packer, but MS doesn't seem to host these VLSC installers anywhere publically
#   - the Office365 installers that can be obtained publicly are for 365 licensing only, not compatible with VL
#     and KMS
# - We also may be able to make our customizations more lightweight, but haven't looked into this:
#   https://technet.microsoft.com/en-us/library/cc179027.aspx

$ISOUrl = "http://path/to/custom/office2016/installer.iso"
$FileDownload = "$env:temp\office.iso"

Import-Module BitsTransfer
Start-BitsTransfer -Source $ISOUrl -Destination $FileDownload

$MountedISO = Mount-DiskImage -PassThru $FileDownload
$Vol = Get-Volume -DiskImage $MountedISO
$OfficeRoot = $Vol.DriveLetter + ":"

Invoke-Expression "cmd /c $($OfficeRoot)\setup.exe /adminfile $($OfficeRoot)\office2016-lab.msp"
