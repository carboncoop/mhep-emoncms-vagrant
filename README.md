# My Home Energy Planner (MHEP) Vagrant installer

This [Vagrant](https://www.vagrantup.com/) configuration installs emoncms and My Home Energy Planner.

## Install vagrant

* Install [Vagrant 2.0.1+](https://www.vagrantup.com/downloads.html)

* Install [Virtualbox 5.2.18](https://www.virtualbox.org/wiki/Downloads)

## Run `vagrant up`

It should create a new Ubuntu 18.04 VM and configure everything.

## Access MHEP

* browse to [localhost:8080/emoncms](http://localhost:8080/emoncms)
* login with username `localadmin`, password `localadmin`

## Pinned versions

This installs specific versions of emoncms, MyHomeEnergyPlanner, MHEP_theme:

* emoncms, latest on `stable`: [https://github.com/emoncms/emoncms/commit/a0c672e4dbf7989d79b00758d5c7a0841e6dce8d](//github.com/emoncms/emoncms/commit/a0c672e4dbf7989d79b00758d5c7a0841e6dce8d)

* MyHomeEnergyPlanner: [https://github.com/paulfurley/MyHomeEnergyPlanner/commit/cfab04784a1e7559358556f615ebcf57178b9864](https://github.com/paulfurley/MyHomeEnergyPlanner/commit/cfab04784a1e7559358556f615ebcf57178b9864)

* MHEP_theme: [https://github.com/carboncoop/MHEP_theme/commit/c65e083ef9f072e4c9d5af7ec0e98942a59d0a06](https://github.com/carboncoop/MHEP_theme/commit/c65e083ef9f072e4c9d5af7ec0e98942a59d0a06)
