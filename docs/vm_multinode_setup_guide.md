# VM multinode setup guide

VM multinode setup means that we can configure more vm_host machines and spread VMs across all of them.
All requested vm_hosts have to be added to inventory.ini to section `all` with all relevant info and
to section `vm_host` hostname only.
To configure multinode setup for VM case we need to use two host_vars file templates.


## The first vm_host


The first template host_vars/host-for-vms-1.yml is used for the first vm_host inside vm_host group.
For the first vm_host we need to configure common parameters for the whole multinode deployment.

### VM image


The only common VM image for all VMs inside deployment is supported at the moment
Default VM image version is Ubuntu 22.04 - focal. That version is used when following params are not configured inside host_vars file.

Supported VM image distributions are ['ubuntu', 'rocky']. VM image distribution can be configured via following parameter:

```
vm_image_distribution: "rocky"
```

Supported VM image ubuntu versions ['22.04']. Default is '22.04'.
VM image version for ubuntu can be changed via following parameter:

```
vm_image_version_ubuntu: "22.04"
```

Supported VM image rocky versions ['8.5', '9.0']. Default is '8.5'.
VM image version for rocky can be changed via following parameter:

```
vm_image_version_rocky: "9.0"
```

### DHCP configuration


dhcp for vxlan have to be enabled just on the first vm_host. "VXLAN tag" inside dhcp list means that DHCP will be configured for that VXLAN.
The same VXLAN tag have to be used inside `vms` definitions on all vm_hosts for all VMs. Param to be set there is vxlan: 128

```
dhcp:
  - 128
```

```
vms:
  - type: ...
    ...
    vxlan: 128
```

DHCP will use following IP range to assign IPs for all VMs. Unique IP range should be used for additional deployments on the same physical network.

```
vxlan_gw_ip: "172.31.0.1/24"
```

## Other vm_hosts except the first one
The second template host_vars/host-for-vms-2.yml is used for all other vm_hosts inside vm_host group.

### DHCP configuration


Secondary vm_host - do not change dhcp settings here
dhcp list have to remain empty here

```
dhcp: []
```

The same VXLAN tag, which was configured for the first vm_host to be used inside `vms` definitions on all vm_hosts for all VMs.
Param to be set there is vxlan: 128

```
vms:
  - type: ...
    ...
    vxlan: 128
```

## Common configuration for all vm_hosts


### VXLAN physical network


vxlan_physical_network parameter specifies IP subnet. IP from this subnet have to be available on one network interface on every VM hosts.
Based on that IP address is automatically detected corresponding network interface name, which is used to setup vxlan network for VMs.
This interface has to be connected to physical network, which is available on all VM hosts.
This parameter is mandatory for VM multinode setup. For VM single node setup it is optional.

e.g.:

```
vxlan_physical_network: "10.31.0.0/16"
```


### VM password


Set hashed password for root user inside VMs. Current value is just placeholder.
To create hashed password use e.g.: openssl passwd -6 -salt SaltSalt <your_password>
The placeholder have to be replaced with real hashed password value.

```
vm_hashed_passwd: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

### Reserved number of CPUs for host OS


cpu_host_os will change number of CPUs reserved for host OS. Default value is 16
It is for experts only who do performance benchmarking. Let it commented out.

```
#cpu_host_os: 8
```
