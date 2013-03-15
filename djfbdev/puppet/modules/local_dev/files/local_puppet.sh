#!/bin/bash
FACTER_fqdn=local.mellowmorning.com puppet apply /vagrant/djfbdev/puppet/manifests/local_dev.pp --modulepath /vagrant/djfbdev/puppet/modules