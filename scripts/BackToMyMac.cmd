REM Test skipping this part to see if our scheduled task will work the first try, leave deferred restart to "give it time"
REM Bootcamp schedules a very short winsat run on the next boot, so leave up to 60 seconds for this to run
REM We don't actually need to explicitly set the startup disk as we now do this automatically on every boot
REM "%ProgramFiles%\Boot Camp\Bootcamp.exe" -StartupDisk

REM So, all we need to actually do here is just clean up and reboot
shutdown -r -t 60 -f

REM Clean ourselves up
rd /s /q "%SystemDrive%\Extras"
