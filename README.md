# winclone-image-builder

This repo is a collection of tools and scripts that can be used to automatically build a Windows image from start to finish in a virtual machine, and was written for imaging Windows onto labs of Mac computers. By default it will build the image in a format compatible with [Winclone](https://twocanoes.com/products/mac/winclone) or [DeployStudio](http://www.deploystudio.com). [Winclone Pro](https://twocanoes.com/products/mac/winclone#pro) also supports installing these images via a self-extracting bundle-style macOS installer package, which this tool can also produce.

It can also output the image in WIM format, using [wimlib](https://wimlib.net) tools to build the image.

This particular image is used in dual-boot labs managed by this project's maintainer. It is a fully up-to-date Windows 10 LTSB installation including Office 2016, Sophos and the BootCamp drivers. LTSB isn't strictly required, but it's what we're using currently.

The particular sequence of steps to build the image is quite site-specific and I've tried where possible to leave the scripts intact but to remove any links to internal locations and credentials. You may choose to omit some of these steps (for example installing your own custom Office) and just comment them out. If the image build and capture process used in this project were better documented, it would be easier to know exactly how to remove these steps or further customize the image, but for now this project assumes a familiarity with Windows OSD deployment, Sysprep, PowerShell, etc.

The Windows Packer template and several scripts (mainly `win-updates.ps1`) are mostly borrowed from the excellent [joefitzgerald/packer-windows](https://github.com/joefitzgerald/packer-windows) and [dylanmei/packer-windows-templates](https://github.com/dylanmei/packer-windows-templates) repos, with some additions. These templates and scripts were borrowed from these repos around spring 2016, so there may be newer changes in their source repos.

## Outline

All tasks are driven by a simple Python script, `run_build.py`, which supports different "steps." The following is a rough outline of the steps this project can perform. See the "More Details" section further down for more on each step.

### build

Builds a Windows VM using Packer. The VM will install Windows, Office 2016, run updates and then self-sysprep using the `unattend_capture.xml` answer file.

### capture

Uses Vagrant to attach the virtual disk that was built in the previous step to an Ubuntu VM, then uses either `ntfsprogs` and `pigz` (parallel gzip) to make an image file compatible with Winclone's command-line tools, or `wimlib` to make a WIM image restorable using other standard Windows imaging tools.

### winclone_bundle

Copies a list of resources out of `/Applications/Winclone Pro.app` so as to make a self-extracting Winclone bundle. This bundle can be restored using Winclone or DeployStudio (or your own tools).

### winclone_package

Wraps this bundle in a payload-free package template derived from the one included in Winclone Pro, and with an option to use a modified `postflight` script.

### pkg_dmg

Wrap the bundle-style package in a read-only DMG. Wrapping in a UDZO (gzip-compressed) DMG saves almost no space, as the Windows image itself is already gzip-compressed, so read-only (not compressed) is used.

### munki

Import the DMG into Munki, setting custom metadata and scripts for the pkginfo. These custom scripts are somewhat site-specific and can be found in the `munki`. They shouldn't be absolutely required for the image to install, but it may be helpful to see what we've done for handling removal of the image, for example.

## Requirements

The following components are required. In parentheses are the currently tested
versions of all the tools:

* Packer (0.12.1)
* Vagrant (1.9.1)
* `puphpet/ubuntu1404-x64` Vagrant box version `20151201` (this box supports both `vmware-desktop` and `virtualbox` providers)
* VirtualBox (5.1.12)
* Winclone Pro (5.7.6)
* Windows 10 Enterprise LTSB ISO (2015 or 2016)
* optional: Munki tools installed on the build system, for `munkiimport`, if using the `munki` step
* optional: VMware Fusion (7 or 8) and the (paid) HashiCorp Vagrant Fusion provider, if you prefer to use VMware Fusion over VirtualBox (`--platform vmware`)

You'll need to download Winclone Pro and copy the .app to `/Applications`, and make sure it's licensed (and that your license for Winclone Pro permits deploying the package to the given number of machines).

## Usage

1. Clone this repo and install all the requirements above.
1. Copy the Windows 10 LTSB ISO into the `iso` directory, or use a custom http URL with your desired ISO.
1. Open `answer_files/10/Autounattend.xml` and put the plaintext local admin password where you see `PLAINTEXT_ADMIN_PASSWORD`. Yes, it has to be plaintext in this one location, as far as I've been able to determine. You'll also need the base64-encoded password in several places where you see `ENCODED_ADMIN_PASSWORD`.
1. If you want to import the final built package into Munki, you'll need to install Munki tools and run `munkiimport --configure`, and mount the repo prior to running the build (it will check this up front and fail otherwise)
1. Finally, run the build with all the steps (you can also use `--platform vmware` if you have VMware Fusion and the HashiCorp `vagrant-vmware-fusion` plugin installed):

`./run_build.py --step all --template windows_10.json`

## More details on steps

### build

With Packer, normally one would build an image and let Packer finish the build by sending the VM a shutdown command via a communicator: SSH or WinRM. The `run_build.py` wrapper script actually sends SIGKILL to Packer's build process once it detects that the VM build is done, monitoring the process table to know when it's safe to do so. This is done so as to avoid requiring _any_ SSH or WinRM configuration or communication to the VM.

WinRM generally works, but requires a bunch of configuration I didn't want to have to later undo, and I've also experienced reliability issues with doing sysprep shutdowns over WinRM. Usually hacky workarounds involving sleep and reboots have been required, and there've been a history of open issues on this in both `mitchellh/packer` (and its predecessor WinRM support in [packer-community/packer-windows-plugins](https://github.com/packer-community/packer-windows-plugins)) and `joefitzgerald/packer-windows` related to expected exit codes, etc. and they have been frustrating to diagnose in that they are done at the end of a lengthy build process. In the end, I found it much simpler to just avoid WinRM configuration altogether in this particular case, and just do what's needed all within `AutoUnattend.xml`, which includes the sysprep shutdown at the end of its run.

Here are steps explaining the actual Windows image creation. See "Image Restoration" later for more details on what automation steps happen after

1. Packer creates and boots the VM, copying various scripts and files to an attached floppy device.
1. The installer environment loads `Autounattend.xml`, which instructs it to format the virtual disk and runs the installation.
1. UAC is disabled because there will later be configurations (or installations) that will take place within the `oobeSystem` phase which are problematic to be automated if UAC is still enabled. It will be re-enabled later during the build.
1. The Autounattend `oobeSystem` defines the creation of our local admin user, skips a few OOBE dialogs, sets an autologon for this new user, then sets a number of scripts to run to on this first login. These include copying files over from the floppy which will be needed within the final image for post-imaging installations like BootCamp drivers and Sophos. This also includes installing a custom Office 2016 package. The final step is a `win-updates.ps1` script, which will check and install Microsoft updates and reboot on a loop until there are no updates left. The script will call a `Finish` function which does a few remaining steps as part of the build:
1. UAD is re-enabled, extraneous files are cleaned up, the Windows update service is restarted.
1. Sysprep is called, passing it the `unattend_capture.xml` answer file.
1. Because sysprep itself will shutdown the VM instead of the conventional Packer remote command, `run_build.py` waits to see the VM process go away and kills the Packer parent process.
1. A new Ubuntu Vagrant box is set up, and the VM disk that was just finished is attached to it.
1. The box is booted and a single shell provisioner runs, capturing and compressing the image in a format compatible with Winclone Pro's `ntfsprogs`-based self-extracting tools. There is also an option in `run_build.py` (`--image-format`) to instead capture this image in WIM format as opposed to Winclone.

### winclone_package

This step will copy over Winclone Pro's `PackageSkel` resource dir into a new directory called `winclone_resources`. If you place a custom `postflight` installer script at `winclone_resources/custom/postflight` (make sure it is executable), this script will copy this custom postflight script into the final image self-extracting bundle, overwriting the one included with Winclone Pro.

One thing you may wish to do in such a custom postflight script is to pre-set the computer name in a sysprep unattend XML using a script similar to what [DeployStudio's NTFS restore task does](https://github.com/timsutton/DeployStudioDiffs/blob/master/Packages/Admin/DeployStudio%20Admin.app/Contents/Frameworks/DSCore.framework/Versions/A/Resources/Tools/ntfsrestore.sh#L207-L237).

It is also worth noting that the installer package produced by this step will be set to create the Windows partition. In the GUI, Winclone offers the option to have the installer package create the partition or to rely on an existing one, and in this case it's going to pick the first option.

Currently the disk size for the Windows volume is 80GB, and its package identifier is `com.github.winclone-image-builder.Windows10` - hardcoded in `run_build.py`. The package version will be of the format `YYYY.MM.DD`.

## munki

THe options for the `munki` step are all configured as options passed to `munkiimport`, which are currently all hardcoded in `run_build.py`. These include several additional scripts, which I don't recommend for general use, but rather that you audit them and decide whether they're appropriate or if you have improvements to make. They make certain assumptions about the environment in which they're being installed. I also don't like that they parse standard diskutil output rather than parsing `-plist` output and would not consider that safe for general use.

## Image Restoration

See `answer_files/10/unattend_capture.xml` for all the details on the Sysprep configured for restore (this includes binding to AD, creating another local user). You would want to customize this for your needs.

Eventually, when the image is restored to a client machine, the `oobeSystem` pass in Sysprep will do an automatic login as the admin user, install BootCamp drivers for this model automatically via `BootCamp.ps1` using [Brigadier](https://github.com/timsutton/brigadier), install our custom Sophos package, and reboot. The `BackToMyMac.cmd` is a script we used to run in order to permanently set the boot volume to the OS X volume by invoking the `BootCamp.exe -StartupDisk` command. We don't do this during the Sysprep phase anymore, so this script has those commands commented out and simply reboots the machine. One of the steps in `BootCamp.ps1` sets the `BootCamp.exe -StartupDisk` command to run as a scheduled task at startup.

The `BootCamp.exe` tool still seems to work (in our testing) in order to configure the boot volume, but according to my sources it is not officially supported by Apple as a CLI utility for doing this.


## Notes on SIP

The postflight script included in this repo assumes that it will be able to write to the MBR, and for this, SIP must be disabled if deploying on 10.11 or later. There are tricks to getting around this by partitioning the boot volume yourself with a stub partition so that OS X will automatically create a guard MBR (rather than a legacy MBR) - see Twocanoes's [blog post on the topic](http://blog.twocanoes.com/post/130271331763/how-el-capitan-boot-camp-is-affected-by-apples), but I've not tested whether performing these steps ahead of time will result in a successful restore by Winclone. If you handle the partitioning yourself prior to installing this image (using the method above or via a Netboot environment, for example), then you shouldn't need SIP disabled to restore this image on a regular booted OS.
