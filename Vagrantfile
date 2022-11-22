Vagrant.configure("2") do |config|
  config.vm.box = "perk/ubuntu-2204-arm64"
  config.vm.synced_folder "./", "/vagrant", create: true, type: "rsync"
  config.vm.provision "shell", path: "scripts/vagrant-provision.sh"
  config.vm.provider "qemu"
end
