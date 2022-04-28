Vagrant.configure("2") do |config|
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--usb", "on"]
    vb.customize ["modifyvm", :id, "--usbehci", "off"]
  end
  config.vm.network "public_network"  
  config.vm.box = "ppadron/raspbian"
  config.vm.provision "shell", path: "scripts/vagrant-provision.sh"
end
