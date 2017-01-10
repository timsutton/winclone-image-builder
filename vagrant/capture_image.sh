#!/bin/bash

OUTPUT_IMAGE_FORMAT="$1"
OUTPUT_PATH="$2"

apt-get update

# winclone output
if [ "$OUTPUT_IMAGE_FORMAT" == "winclone" ]; then
	apt-get install -y pigz
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
	apt-get install -y wimtools
	WIMLIB_IMAGEX_USE_UTF8=1 wimcapture /dev/sdb1 "${OUTPUT_PATH}" --boot
fi
