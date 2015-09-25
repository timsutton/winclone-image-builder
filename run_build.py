#!/usr/bin/python

import optparse
import os
import re
import shutil
import subprocess
import sys
import time

from glob import glob
from pprint import pprint


class VMManagementError(Exception):
    pass


def executable_in_path(executable):
    '''Returns the full path to an executable according to PATH,
    otherwise None.'''
    path = os.environ.get('PATH')
    if not path:
        print >> sys.stderr, "Warning: No PATH could be searched"
    paths = path.split(':')
    for p in paths:
        fullpath = os.path.join(p, executable)
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
        key, equals, value = line.split(" ", 2)
        # strip leading and trailing character, which should be double-quotes
        value = value[0:-1][1:]
        vmx[key] = value
    return vmx


def main():
    DEFAULT_PLATFORM = 'vmware'
    VALID_STEPS = [
        'build',
        'capture',
        'selfextractify'
    ]
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
    OUTPUT_IMAGE_FORMATS = ['winclone', 'wim']
    usage = """Tool to perform tasks around building and capturing a Windows
NTFS image.
"""
    o = optparse.OptionParser()
    o.add_option('-s', '--step', action='append',
                 help=("Add a step to the build. Valid steps are: "
                       "%s." % ', '.join(VALID_STEPS)))
    o.add_option('--platform', default=DEFAULT_PLATFORM,
                 help=("Name of VM platform to be used. Defaults to "
                       "'%s'." % DEFAULT_PLATFORM))
    o.add_option('-v', '--verbose', action='count', default=0,
                help="Verbosity output via TOOL_LOG env. Can be given twice.")
    o.add_option('--image-format', default='winclone',
                help=("Desired output image format. One of: %s. Defaults to "
                      "'winclone'. " % ', '.join(OUTPUT_IMAGE_FORMATS)))
    opts, args = o.parse_args()


    run_steps = opts.step
    if not run_steps:
        o.print_usage()
        exit()
    for step in run_steps:
        if step not in VALID_STEPS:
            sys.exit(("%s is not a valid step. See --help for more "
                      "information." % step))

    if opts.image_format and opts.image_format not in OUTPUT_IMAGE_FORMATS:
        print "Invalid image format!!"
        exit()

    proj_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    print "Project dir: %s" % proj_dir
    env = os.environ
    if opts.verbose == 1:
        env['VAGRANT_LOG'], env['PACKER_LOG'] = 'info', 'info'
    if opts.verbose >= 2:
        env['VAGRANT_LOG'], env['PACKER_LOG'] = 'debug', 'debug'

    if 'build' in run_steps:
        if not args:
            o.print_usage()
        template = args[0]
        packer_bin = executable_in_path('packer')
        if not packer_bin:
            sys.exit("No Packer binary could be found in PATH. Exiting.")
        subprocess.call([
                packer_bin,
                'build',
                '-only', PLATFORMS[opts.platform]['packer_builder'],
                '-force',
                template],
            cwd=proj_dir,
            env=env
        )

    if 'capture' in run_steps:
        vagrant_bin = executable_in_path('vagrant')

        # Sanity checks
        if not vagrant_bin:
            sys.exit("No Vagrant binary could be found in PATH. Exiting.")
        
        if opts.platform not in PLATFORMS:
            sys.exit("--platform '%s' not one of those supported: %s" %
                    (opts.platform, ', '.join(PLATFORMS.keys())))
        if 'vagrant_plugins' in PLATFORMS[opts.platform]:
            p = subprocess.Popen([vagrant_bin, 'plugin', 'list'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
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


        # Get the path to the VMDK that was just built
        # - currently naively assuming Packer's default output directory for
        #   an 'unnamed' VM, according to builder type
        packer_vm_dir = os.path.join(
                            proj_dir,
                            'output-%s' % \
                                PLATFORMS[opts.platform]['packer_builder'])
        # vmware: read the vmdk name from the VMX
        if opts.platform == 'vmware':
            vmxpath = os.path.join(packer_vm_dir, 'packer-vmware-iso.vmx')
            vmx = load_vmx(vmxpath)
            win_vmdk_path = os.path.join(packer_vm_dir, vmx['scsi0:0.filename'])
        # virtualbox: for now just glob for a vmdk in the packer vm dir
        # - probably better would be to run the appropriate VBoxManage command
        if opts.platform == 'virtualbox':
            win_vmdk_path = glob(packer_vm_dir + '/*.vmdk')[0]
        
        print "Located VMDK at path: %s" % win_vmdk_path

        # Setup environment vars for this Vagrant instantiation
        env["VMDK_PATH"] = win_vmdk_path
        env["OUTPUT_IMAGE_FORMAT"] = opts.image_format
        env["VAGRANT_DEFAULT_PROVIDER"] = \
            PLATFORMS[opts.platform]['vagrant_provider']

        # Vagrant up
        subprocess.call([
                vagrant_bin,
                'up'],
            cwd=proj_dir,
            env=env
        )

        # Vagrant destroy
        subprocess.call([
                vagrant_bin,
                'destroy',
                '--force'],
            cwd=proj_dir,
            env=env
        )

    if 'selfextractify' in run_steps:
        wc_res_dir = os.path.join(proj_dir, 'winclone_resources')
        image_bundle_path = os.path.join(proj_dir, 'image.winclone')
        ntfs_image_name = 'boot.img.gz'
        ntfs_image_path = os.path.join(proj_dir, ntfs_image_name)
        if not os.path.exists(ntfs_image_path):
            exit("Expected NTFS image at %s but none was found. Exiting." %
                 ntfs_image_path)

        if os.path.exists(image_bundle_path):
            shutil.rmtree(image_bundle_path)
        os.mkdir(image_bundle_path)
        os.rename(ntfs_image_path, os.path.join(
                    image_bundle_path, ntfs_image_name))
        for res_file in os.listdir(wc_res_dir):
            print "Copying resource: %s" % res_file
            shutil.copy(
                os.path.join(wc_res_dir, res_file),
                image_bundle_path)


if __name__ == '__main__':
    main()
