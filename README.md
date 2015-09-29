# winclone-image-builder

This repo contains some tools which can be used to automatically build a Windows image that can be restored onto a physical Mac.

These are:

* Packer template, heavily borrowed from [joefitzgerald/packer-windows](https://github.com/joefitzgerald/packer-windows) and [dylanmei/packer-windows-templates](https://github.com/dylanmei/packer-windows-templates)
* Vagrantfile
* A wrapper script, `run_build.py`, which can automate the several phases required to prepare the final image

This seems to work mostly for Windows 7 and Windows 10, but because I've had minor issues with these I'm currently only including a Windows 8.1 template. I've confirmed Windows 7 to work as well, though it's not yet included here.

## Build phase

`./run_build.py [--platform <option>] -s build`

The Packer template is very close to those provided in Joe Fitzgerald's packer-windows repo. A couple key additions, however: there are some post-restore actions to install Boot Camp drivers using [Brigadier](https://github.com/timsutton/brigadier), and for use with older versions of Windows, a sample of copying the ethernet drivers from several Boot Camp ESDs to be included in `C:\Windows\INF` so that on initial restore they are present and loaded for Brigadier's Boot Camp installation process. This is particularly required for Windows 7, which does not have many of the needed Ethernet drivers.

## Capture phase

`./run_build.py [--platform <option>] -s capture`

This performs a search for the built .vmdk that was attached to the Packer VM, and sets an environment variable containing this path before starting a Vagrant VM. This Vagrant environment includes commands to attach the .vmdk to the OS as a second disk. The VM runs a script to install `ntfsprogs` on Ubuntu, and captures the Windows volume to a path that's reachable via Vagrant's synced folder. The volume will be in the same gzipped format that is used by Winclone when it creates images.

## Selfextractify phase

`./run_build.py -s selfextractify`

This step requires a one-time setup on your part, at least for the time being. Some additional resources are included with WinClone Pro to build a "self-extracting" image that's in a bundle format: a directory ending in ".winclone". You must create a folder in this repository root called `winclone_resources`, and place all the required files in it. You will find these files within `Winclone Pro.app/Contents/Resources`. Eventually this tool will be updated to be able to automatically copy these out from an installed copy of Winclone, but for now this step is required.

```
BCD
EFIBCD
blocksize
boot.mbr
genericboot.mbr
gptrefresh
hiberfil.sys
ntfscat
ntfsclone
ntfscmp
ntfscp
ntfsinfo
ntfsresize
partitionid
pigz
winclone_helper_tool
```

The `run_build.py` script will then copy out all of these files from `winclone_resources` in a new bundle directory, and move the `boot.img.gz` file into this new bundle, resulting in a complete, self-extracting Winclone image.

## Dependency on Winclone

Currently this tool explicitly requires Winclone, and it's in theory possible to have it instead output the image in a structure that DeployStudio is able to use to deploy the NTFS image. I highly recommend anyone doing Windows deployment on OS X look at buying at least the Winclone Pro license, however.
