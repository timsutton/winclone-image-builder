# Do Boot Camp installation
Invoke-Expression "cmd /c C:\Extras\brigadier.exe --install"

# Make a scheduled task that sets the boot volume to OS X on every system start
# - `bless --nextonly` seems to break boot selection entirely on 10.11, so we
#   are blessing the Windows volume "permanently" when telling the system to
#   boot into Windows. This lets us set it back immediately. If Windows's
#   install is broken, however, the system will need to be set manually back
#   to OS X.
#
# If you don't want to install any such scheduled tasks or have some other way
# to manage alternate OS booting (or don't want to), just comment or delete
# these lines.

$jobname = 'SetMacBoot'
# Not expanding ProgramFiles during script execution, saner to let the system figure it out at run time
$action = New-ScheduledTaskAction -Execute "%ProgramFiles%\Boot Camp\Bootcamp.exe" -Argument '-StartupDisk'
$trigger = New-ScheduledTaskTrigger -AtStartup
$principal = New-ScheduledTaskPrincipal -UserID 'NT AUTHORITY\SYSTEM' -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask $jobname -Action $action -Trigger $trigger -Principal $principal
