# -*- mode: ruby -*-
# vi: set ft=ruby :

require 'rubygems'
require 'json'

def configure_box(index, config)
  name = "local_dev-#{index}".intern
  config.vm.customize ["modifyvm", :id, "--memory", 1024*2]
  ip = "192.168.50.42"
  
  config.vm.define name do |slave_conf|
    slave_conf.vm.box = "precise"
    slave_conf.vm.box_url = "http://files.vagrantup.com/precise64.box"
    slave_conf.vm.network :hostonly, ip

  slave_conf.vm.provision :puppet do |puppet|
    puppet.manifests_path = "djfbdev/puppet/manifests"
    puppet.module_path = "djfbdev/puppet/modules"
    puppet.manifest_file = "local_dev.pp"
    puppet.options = "--verbose --debug"
    facts = {
      :ec2_userdata => {
        :role => 'local_dev',
        :environment => 'development'
      }.to_json,
      :vagrant => true,
      :ip => ip
    }
    puppet.facter = facts
  end

  end
end

Vagrant::Config.run do |config|
   1.times do |i|
     configure_box(i, config)
   end
end
