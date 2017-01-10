#!/bin/bash

OUTPUT_IMAGE_FORMAT="$1"
# this should be the synced folder root
OUTPUT_DIR=/vagrant/

apt-get install -y pigz

# winclone output
if [ "$OUTPUT_IMAGE_FORMAT" == "winclone" ]; then
	OUTPUT_PATH="${OUTPUT_DIR}/boot.img.gz"
	# Clone and pipe through pigz
	ntfsclone \
		--quiet \
		--save-image \
		--output - \
		/dev/sdb1 | \
	pigz > "${OUTPUT_PATH}"
fi

# wim output
if [ "$OUTPUT_IMAGE_FORMAT" == "wim" ]; then
	OUTPUT_PATH="${OUTPUT_DIR}/boot.wim"
	apt-get install -y wimtools
	WIMLIB_IMAGEX_USE_UTF8=1 wimcapture /dev/sdb1 "${OUTPUT_PATH}" --boot
fi
