# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "puphpet/ubuntu1404-x64"

  # add second VMDK to the Fusion VM
  config.vm.provider "vmware_fusion" do |v|
    v.gui = true
    v.vmx["scsi0:1.present"]  = "TRUE"
    v.vmx["scsi0:1.filename"]  = ENV["VMDK_PATH"]
  end

  config.vm.provider "virtualbox" do |v|
    v.gui = true
    v.customize ["storageattach", :id, "--storagectl", "IDE Controller", "--port", "0", "--device", "1", "--type", "hdd", "--medium", ENV["VMDK_PATH"]]
  end

  config.vm.provision "shell", path: "scripts/capture_image.sh", args: ENV["OUTPUT_IMAGE_FORMAT"]
end
