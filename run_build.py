#!/usr/bin/python

# disabling Pylint variable warnings, missing docstrings and "too many" things
# pylint: disable-msg=C0103
# pylint: disable-msg=C0111
# pylint: disable-msg=R0912,R0914,R0915
# disable warnings for Foundation and missing mobule members
# pylint: disable-msg=E0611

import optparse
import os
import plistlib
import shutil
import subprocess
import sys
import time

from glob import glob

class VMManagementError(Exception):
    pass

# borrowed from Munki:
# https://github.com/munki/munki/blob/c3485f2ab04458eb061e26dd656a0c526295aadd/code/client/munkilib/utils.py
def get_pid_for_process_name(processname):
    '''Returns a process ID for processname'''
    cmd = ['/bin/ps', '-eo', 'pid=,command=']
    try:
        proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    except OSError:
        return 0

    while True:
        line = proc.stdout.readline().decode('UTF-8')
        if not line and (proc.poll() != None):
            break
        line = line.rstrip('\n')
        if line:
            try:
                (pid, process) = line.split(None, 1)
            except ValueError:
                # funky process line, so we'll skip it
                pass
            else:
                if process.find(processname) != -1:
                    return str(pid)

    return 0


def executable_in_path(executable):
    '''Returns the full path to an executable according to PATH,
    otherwise None.'''
    path = os.environ.get('PATH')
    if not path:
        print >> sys.stderr, "Warning: No PATH could be searched"
    paths = path.split(':')
    for path in paths:
        fullpath = os.path.join(path, executable)
        if os.path.isfile(fullpath) and os.access(fullpath, os.X_OK):
            return fullpath
    return None


def load_vmx(path_to_vmx):
    '''Given the path to a VMX file, return a dict with its options and
    values.'''
    data = open(path_to_vmx, 'r').read().splitlines()
    vmx = dict()
    for line in data:
        # split by spaces, only twice
        key, _, value = line.split(" ", 2)
        # strip leading and trailing character, which should be double-quotes
        value = value[0:-1][1:]
        vmx[key] = value
    return vmx


def main():
    DEFAULT_PLATFORM = 'virtualbox'

    # VALID_STEPS is the list of all steps we know how to perform. This list
    # should be kept in logical order so that we can pass in a special 'all'
    # step and these will simply be run in the list order.
    VALID_STEPS = (
        'build',
        'capture',
        'winclone_bundle',
        'winclone_package',
        'pkg_dmg',
        'munki',
        'all'
    )
    PLATFORMS = {
        'vmware': {
            'packer_builder': 'vmware-iso',
            'vagrant_provider': 'vmware_fusion',
            'vagrant_plugins': ['vagrant-vmware-fusion'],
        },
        'virtualbox': {
            'packer_builder': 'virtualbox-iso',
            'vagrant_provider': 'virtualbox',
        },
    }
    OUTPUT_IMAGE_FORMATS = ('winclone', 'wim')
    IMAGE_FILE = 'image.winclone'

    usage = """Tool to perform tasks around building and capturing a Windows
NTFS image. You must add at least one step using the `-s` option, and more
than one can be added in one run. Some
"""
    o = optparse.OptionParser(usage=usage)
    o.add_option('-s', '--step', action='append',
                 help=("Add a step to the build. Valid steps are: "
                       "%s. The special step 'all' will run all steps."
                       % ', '.join(VALID_STEPS)))
    o.add_option('--platform', default=DEFAULT_PLATFORM,
                 help=("Name of VM platform to be used for 'build' and "
                       "'capture steps. Defaults to '%s'." % DEFAULT_PLATFORM))
    o.add_option('-v', '--verbose', action='count', default=0,
                 help="Verbosity output via TOOL_LOG env. Can be given twice.")
    o.add_option('-t', '--template',
                 help=("Packer template to use for the 'build' step. Required "
                       "if 'build' is specified as a step."))
    o.add_option('--image-format', default='winclone',
                 help=("Desired output image format for the 'capture' step."
                       ". One of: %s. Defaults to 'winclone'. "
                       % ', '.join(OUTPUT_IMAGE_FORMATS)))
    opts, _ = o.parse_args()


    run_steps = opts.step
    if not run_steps:
        o.print_usage()
        exit(-1)

    for step in run_steps:
        if step not in VALID_STEPS:
            sys.exit(("%s is not a valid step. See --help for more "
                      "information." % step))

    if 'all' in run_steps:
        run_steps = VALID_STEPS

    if opts.image_format and opts.image_format not in OUTPUT_IMAGE_FORMATS:
        exit("Invalid image format!")

    # Sanity check 'build' opts
    if 'build' in run_steps:
        template = opts.template
        if not template:
            exit("'build' step requires specifying the '-t/--template' option "
                 "to specify a Packer template to use.")

    # Sanity check 'capture' opts and Vagrant environment
    if 'capture' in run_steps:
        vagrant_bin = executable_in_path('vagrant')

        if not vagrant_bin:
            sys.exit("No Vagrant binary could be found in PATH. Exiting.")

        if opts.platform not in PLATFORMS:
            sys.exit("--platform '%s' not one of those supported: %s" %
                     (opts.platform, ', '.join(PLATFORMS.keys())))
        if 'vagrant_plugins' in PLATFORMS[opts.platform]:
            p = subprocess.Popen([vagrant_bin, 'plugin', 'list'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, _ = p.communicate()
            plugins = [x.split(' ', 1)[0] for x in out.splitlines()]
            for req_plugin in PLATFORMS[opts.platform]['vagrant_plugins']:
                missing_plugins = False
                if req_plugin not in plugins:
                    print >> sys.stderr, \
                             ("The '%s' platform requires the '%s' Vagrant "
                              "plugin to be installed.") % (
                                  opts.platform, req_plugin)
                    if not missing_plugins:
                        missing_plugins = True
                if missing_plugins:
                    sys.exit(1)

    # Sanity check Munki environment
    if 'munki' in run_steps:
        munkiimport_bin = '/usr/local/munki/munkiimport'
        if not os.path.exists(munkiimport_bin):
            sys.exit("Step 'munki' requires Munki tools to be installed at "
                     "the default /usr/local/munki location.")
        from Foundation import CFPreferencesCopyAppValue
        repo_path = CFPreferencesCopyAppValue(
            'repo_path', 'com.googlecode.munki.munkiimport')
        if not repo_path:
            sys.exit("Step 'munki' requires munkiimport to be configured. "
                     "Please run `munkiimport --configure` to set it up first.")
        if not os.path.isdir(repo_path):
            sys.exit("Please mount the Munki repo path at '%s' before running "
                     "the build." % repo_path)

    proj_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    print "Project dir: %s" % proj_dir
    env = os.environ
    if opts.verbose == 1:
        env['VAGRANT_LOG'], env['PACKER_LOG'] = 'info', 'info'
    if opts.verbose >= 2:
        env['VAGRANT_LOG'], env['PACKER_LOG'] = 'debug', 'debug'

    wc_res_source = '/Applications/Winclone Pro.app/Contents/Resources'
    wc_res_dir = os.path.join(proj_dir, 'winclone_resources')

    pkg_bundle_filename = 'WincloneWindows10_Lab.pkg'
    pkg_dmg_filename = 'WincloneWindows10_Lab.dmg'

    if 'build' in run_steps:
        packer_bin = executable_in_path('packer')
        if not packer_bin:
            sys.exit("No Packer binary could be found in PATH. Exiting.")

        packer_builder = PLATFORMS[opts.platform]['packer_builder']
        cmd = [packer_bin,
               'build',
               '-only', packer_builder,
               '-force',
               template]
        proc = subprocess.Popen(cmd, cwd=proj_dir, env=env)

        # Maybe naive, but most likely the proc we're looking for needs to
        # contain only: 'packer-<builder_name>' in its arg list
        process_snippet = 'packer-' + packer_builder

        pid = True

        # horrible hack to wait for any Packer steps prior to booting the VM
        # what we should really do is first have a loop to wait for the VM
        # process to _start_, and then we enter the loop waiting for it to end,
        # all the while checking the status of proc
        time.sleep(300)

        while pid:
            time.sleep(3)
            # pid will be 0 once the process no longer exists.
            pid = get_pid_for_process_name(process_snippet)
#            print "%s builder has pid %s" % (packer_builder, pid)

        print "Process done, killing.."
        proc.kill()


    if 'capture' in run_steps:
        vagrant_bin = executable_in_path('vagrant')
        vagrant_dir = os.path.join(proj_dir, 'vagrant')

        # Get the path to the VMDK that was just built
        # - currently naively assuming Packer's default output directory for
        #   an 'unnamed' VM, according to builder type
        packer_vm_dir = os.path.join(proj_dir,
                                     'output-%s' % \
                        PLATFORMS[opts.platform]['packer_builder'])
        # vmware: read the vmdk name from the VMX
        if opts.platform == 'vmware':
            vmxpath = os.path.join(packer_vm_dir, 'packer-vmware-iso.vmx')
            vmx = load_vmx(vmxpath)
            env["VMDK_PATH"] = os.path.join(packer_vm_dir, vmx['scsi0:0.filename'])
            # env["VMDK_PATH"] = win_vmdk_path

        # virtualbox: for now just glob for a vmdk in the packer vm dir
        # - probably better would be to run the appropriate VBoxManage command
        if opts.platform == 'virtualbox':
            env["VDI_PATH"] = glob(os.path.join(packer_vm_dir, '*.vdi'))[0]
            # win_vmdk_path = glob(packer_vm_dir + '/*.vmdk')[0]

        img_file = 'boot.img.gz'
        if opts.image_format == 'wim':
            img_file = 'boot.wim'

        # Setup environment vars for this Vagrant instantiation
        env["OUTPUT_IMAGE_FORMAT"] = opts.image_format
        env["VAGRANT_DEFAULT_PROVIDER"] = \
            PLATFORMS[opts.platform]['vagrant_provider']

        img_output_root = '/vagrant'
        env["OUTPUT_PATH"] = os.path.join(img_output_root, img_file)

        # Vagrant up
        subprocess.check_call([vagrant_bin, 'up'], cwd=vagrant_dir, env=env)

        # Vagrant destroy
        subprocess.check_call([vagrant_bin, 'destroy', '--force'],
                              cwd=vagrant_dir,
                              env=env
                             )

        # Save artifact to the project root
        artifact_dest = os.path.join(proj_dir, img_file)
        if os.path.exists(artifact_dest):
            os.remove(artifact_dest)
        os.rename(os.path.join(vagrant_dir, img_file), artifact_dest)

    if 'winclone_bundle' in run_steps:
        if not os.path.isdir(wc_res_source):
            exit("This build step requires Winclone Pro.app to exist at %s."
                 % wc_res_source)
        # blocksize, size, BCD (for EFI at least) not needed it seems
        wc_support_files = [
            'EFIBCD',
            'genericboot.mbr',
            'gptrefresh',
            'hiberfil.sys',
            'ntfscat',
            'ntfsclone',
            'ntfscp',
            'ntfsinfo',
            'ntfsresize',
            'pigz',
            'winclone_helper_tool',
        ]
        # bundle_res_dir = os.path.join(wc_res_dir, 'bundle')
        image_bundle_path = os.path.join(proj_dir, IMAGE_FILE)
        ntfs_image_name = 'boot.img.gz'
        ntfs_image_path = os.path.join(proj_dir, ntfs_image_name)
        if not os.path.exists(ntfs_image_path):
            exit("Expected NTFS image at %s but none was found. Exiting." %
                 ntfs_image_path)

        if os.path.exists(image_bundle_path):
            shutil.rmtree(image_bundle_path)
        os.mkdir(image_bundle_path)

        shutil.copy(ntfs_image_path,
                    os.path.join(image_bundle_path, ntfs_image_name))
        for res_file in wc_support_files:
            print "Copying resource: %s" % res_file
            shutil.copy(
                os.path.join(wc_res_source, res_file),
                image_bundle_path)

        # Copy or set additional resources:

        ## winclone_helper_tool is setuid when originally installed with
        ## Winclone Pro.app, but it won't run with those permissions at the
        ## CLI (just says "must be root")
        os.chmod(os.path.join(image_bundle_path, 'winclone_helper_tool'),
                 0775)
        ## partitionid
        with open(os.path.join(image_bundle_path, 'partitionid'), 'w') as fd:
            # I don't know in what scenario this file would ever be something
            # other than 0x00
            fd.write('0x00')
        ## boot.mbr
        shutil.copy(os.path.join(image_bundle_path, 'genericboot.mbr'),
                    os.path.join(image_bundle_path, 'boot.mbr'))
        ## windows8OrLater
        with open(os.path.join(image_bundle_path, 'windows8OrLater'), 'w') as fd:
            # Not _totally_ sure this is needed for anything but the Winclone
            # Pro GUI
            fd.write('YES')

        # known working bootx64.efi from a clean Windows install that may
        # fix an issue with Windows 10 1511
        # shutil.copy(os.path.join(wc_res_dir, 'custom/efi/bootx64.efi'),
        #             image_bundle_path)

    if 'winclone_package' in run_steps:
        bundle_id = 'com.github.winclone-image-builder.Windows10'
        pkg_version = time.strftime('%Y.%m.%d')
        partition_size = '80024509440'

        if os.path.exists(pkg_bundle_filename):
            shutil.rmtree(pkg_bundle_filename)
        shutil.copytree(os.path.join(wc_res_source, 'PackageSkel'), pkg_bundle_filename)
        pkg_res_dir = os.path.join(pkg_bundle_filename, 'Contents', 'Resources')

        # customize the package identifier and version
        info_plist_path = os.path.join(pkg_bundle_filename, 'Contents', 'Info.plist')
        plist = plistlib.readPlist(info_plist_path)
        plist['CFBundleShortVersionString'] = pkg_version
        plist['CFBundleIdentifier'] = bundle_id
        plistlib.writePlist(plist, info_plist_path)

        # define settings.sh used by postflight
        with open(os.path.join(pkg_res_dir, 'settings.sh'), 'w') as settings_fd:
            settings_fd.write("""#!/bin/sh
mode="create"
mac_device="/dev/disk0s2"
size="%s"
""" % partition_size)

        # copy a custom postflight with our additions and changes
        custom_postflight = os.path.join(wc_res_dir, 'custom', 'postflight')
        if os.path.exists(custom_postflight):
            shutil.copy(custom_postflight, pkg_res_dir)

        # finally, copy the image
        shutil.copytree(IMAGE_FILE, os.path.join(pkg_res_dir, os.path.basename(IMAGE_FILE)))

    if 'pkg_dmg' in run_steps:
        if os.path.exists(pkg_dmg_filename):
            os.remove(pkg_dmg_filename)
        cmd = ['hdiutil', 'create',
               '-srcfolder', pkg_bundle_filename,
               '-format', 'UDRO',
               pkg_dmg_filename]
        subprocess.call(cmd)

    if 'munki' in run_steps:
        cmd = [munkiimport_bin]
        cmd.extend([
            '--nointeractive',
            '--subdirectory', 'windows',
            '--name', 'Windows_Lab',
            '--displayname', 'Windows 10 lab image',
            '--RestartAction', 'RequireRestart',
            '--preinstall_script', 'munki/preinstall_script.sh',
            '--postinstall_script', 'munki/postinstall_script.sh',
            '--uninstall_script', 'munki/uninstall_script.sh',
        ])
        cmd.append(pkg_dmg_filename)
        subprocess.call(cmd)

if __name__ == '__main__':
    main()
