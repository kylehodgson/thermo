Vagrant.configure("2") do |config|
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--usb", "on"]
    vb.customize ["modifyvm", :id, "--usbehci", "off"]
  end
  config.vm.network "forwarded_port", guest: 8888, host: 8888
  config.vm.box = "ppadron/raspbian"
  config.vm.provision "shell", path: "scripts/vagrant-provision.sh"
end
