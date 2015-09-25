#!/bin/sh

./run_build.py -s build --platform virtualbox windows_81.json
./run_build.py -s capture --platform virtualbox
./run_build.py -s selfextractify
open image.winclone
