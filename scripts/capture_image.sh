#!/bin/bash

OUTPUT_IMAGE_FORMAT="$1"
# this should be the synced folder root
OUTPUT_DIR=/vagrant/

# winclone output
if [ "$OUTPUT_IMAGE_FORMAT" == "winclone" ]; then
	OUTPUT_PATH="${OUTPUT_DIR}/boot.img"
	# Clone
	ntfsclone \
		--quiet \
		--save-image \
		--overwrite "${OUTPUT_PATH}" \
		/dev/sdb1
	# Compress
	gzip --force "${OUTPUT_PATH}"
fi

# wim output
if [ "$OUTPUT_IMAGE_FORMAT" == "wim" ]; then
	OUTPUT_PATH="${OUTPUT_DIR}/boot.wim"
	echo "deb http://ppa.launchpad.net/nilarimogard/webupd8/ubuntu trusty main" > /etc/apt/sources.list.d/webupd8.list
	echo "deb-src http://ppa.launchpad.net/nilarimogard/webupd8/ubuntu trusty main" >> /etc/apt/sources.list.d/webupd8.list

	# insert the PGP key for the Launchpad webupd8 repo
	cat << EOF | apt-key add -
-----BEGIN PGP PUBLIC KEY BLOCK-----
Version: SKS 1.1.4
Comment: Hostname: keyserver.ubuntu.com

mI0ES1d9aAEEAN8DBnDfNfBdx79khNBGbxia9xzjOYvV1arktnVoEOo4Od2Tru3RMDTY3Ghg
7LLoQbUGcAq3gPiIlTBLuBT/G2doNPirqP1rcK5VHJyok7CqOZBPjJM4zZEZaJ6luH6Ffizq
X2CYE0j0dxwDwCYt1TJy/06AIB8F7NzbKrTE37wtABEBAAG0EUxhdW5jaHBhZCB3ZWJ1cGQ4
iLYEEwECACAFAktXfWgCGwMGCwkIBwMCBBUCCAMEFgIDAQIeAQIXgAAKCRBTHucvTJ0jTKwc
A/997aeDmJO2ugJ2OnBEI+VPHK8+ojW1PZi9sUGKTzBAEcwrSB0xt9jAvSWK8iedL5xm8WXw
eToIPqp6FyWe7KVfKBh5v6i+kG59nGzlw6wYrcxh33XH+ko0NAPf3tT+tKHNlNyP9QrcdygS
qpm1/uVf/iREmwpzuHfyr/CYrzh/lA==
=EBW3
-----END PGP PUBLIC KEY BLOCK-----
EOF

	# Install tools
	apt-get update
	apt-get install -y wimtools

	wimcapture /dev/sdb1 "${OUTPUT_PATH}" --boot
fi
