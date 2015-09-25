#!/bin/sh

dir=$(dirname ${0})

sudo "${dir}/image.winclone/winclone_helper_tool" \
	 --self-extract \
	 --ntfspartition /dev/disk0s4
sudo bless --setBoot --legacy --device /dev/disk0s4
sudo reboot
