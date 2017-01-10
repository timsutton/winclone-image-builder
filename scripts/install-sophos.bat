"C:\Extras\sophos.exe"
del "C:\Extras\sophos.exe"

REM Add users to SophosPowerUser group, can include domain since we're bound
net localgroup "SophosPowerUser" "Authenticated Users" /add
net localgroup "SophosPowerUser" "Interactive" /add
net localgroup "SophosPowerUser" "MYDOMAIN\Domain Users" /add
