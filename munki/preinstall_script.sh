#!/bin/sh

# The package requires there to be only an HFS+ partition, so we first destroy the
# Windows partition if we're going to install it, growing our HFS+ partition back
ntfs_volume=$(diskutil list | grep "Microsoft Basic Data"|sed 's/.*\(disk.*s.*\)/\1/' | head -n 1)
if [ -n "${ntfs_volume}" ]; then
    # destroy Windows volume and grow us back
    # TODO: we shouldn't assume the volume is mounted here
    diskutil unmount "${ntfs_volume}"

    # remove the partition by setting it to free space
    diskutil eraseVolume "Free Space" "And I'll write your name" "${ntfs_volume}"

    # gross way to get the LV of the last listed partition, our main OS X system
    LV=$(diskutil cs list | grep Logical\ Volume | tail -n 1 | awk '{print $4}')

    diskutil cs resizeStack "$LV" 0g
fi
