#!/bin/sh

ntfs_volume=$(diskutil list | grep "Microsoft Basic Data"|sed 's/.*\(disk.*s.*\)/\1/' | head -n 1)

# bless the Windows partition permanently
/usr/sbin/bless --setBoot --device "/dev/${ntfs_volume}"
