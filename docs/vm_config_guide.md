# VM specific configuration for SRIOV NIC and SRIOV QAT


In order to deploy VM case, VM specific configuration has to be used. It is generated automatically via `make`. It is generated into `examples/vm/` directory. Configurations for each profile are kept in profile named directories. Group vars for VM case have set `vm_enabled` value to `true`. To deploy standard BM RA the configuration files must be re-generated. It is not sufficient to change the value of `vm_enabled` to `false`.

```
vm_enabled: true
```


## vm-host specific options

There's also a set of configuration options that are applied in per-node manner.

First set of variables enables SRIOV for selected network adapters and QAT devices. It requires setting `iommu_enabled` as `true`.

**For SRIOV NIC** it requires passing pci ids of the physical function interfaces together with additional NIC parameters, which contain also an option to define how many virtual functions should be created for each physical function. In below example `dataplane_interfaces` configuration will create 8 VFs for `"18:00.0"` PF interface and attach them to kernel mode `iavf` driver by default and listed vfs (vf_00 and vf_05) attach to selected driver (in our case `vfio-pci` driver). Then it will create 2 VFs for `"18:00.1"` PF interface and attach them to `vfio-pci` driver.

**For SRIOV QAT** it requires passing qat id of the QAT physical function together with an option to define how many virtual functions should be created for each physical function. In below example `qat_devices` configuration will create 12 VFs for `"0000:3d:00.0"` PF device, 10 VFs for `"0000:3f:00.0"` PF device and 10 VFs for `"0000:da:00.0"` PF device.  
**_NOTE:_** Some QAT drivers ignore requested number of VFs and create maximum number of VFs allowed by current QAT device. Where: "0" means no VFs, number between "1" and "max num of VFs" creates max number of VFs and number above "max num of VFs" cause an error.

This setting will also add IOMMU kernel flags, and as a result will reboot the target vm-host during deployment.
```
dataplane_interfaces:
  - bus_info: "18:00.0"
    pf_driver: i40e
    ddp_profile: "gtp.pkgo"
    default_vf_driver: "iavf"
    sriov_numvfs: 8
    sriov_vfs:
      vf_00: "vfio-pci"
      vf_05: "vfio-pci"

  - bus_info: "18:00.1"
    pf_driver: i40e
    ddp_profile: "gtp.pkgo"
    default_vf_driver: "vfio-pci"
    sriov_numvfs: 2

qat_devices:
  - qat_id: "0000:3d:00.0"
    qat_sriov_numvfs: 12

  - qat_id: "0000:3f:00.0"
    qat_sriov_numvfs: 10

  - qat_id: "0000:da:00.0"
    qat_sriov_numvfs: 10

```

Next section provides VM related configuration options.
The first option defines VM image distribution of cloud image, which will be used inside VMs.
  Currently supported distributions are: "ubuntu" and "rocky". Default is "ubuntu"
Following two options define VM image version for Ubuntu and for Rocky.
  Currently supported ubuntu versions are: "20.04" and "22.04". Default is "20.04"
  Currently supported rocky versions are: "8.5" and "9.0". Default is "8.5"
Default VM image distribution is "ubuntu" and default version is "20.04"
Setting for VM image can be done just on the first VM host. It is common for all VMs across all VM hosts.

```
vm_image_distribution: "ubuntu"
vm_image_version_ubuntu: "22.04"
vm_image_version_rocky: "9.0"
```

The next options defines VM networking
dhcp parameter specify `vxlan id`. Dhcp then provides IP addresses to vxlan network identified by `vxlan id`.
In current default configuration `vxlan id` is `120` and `vxlan_gw_ip` is `"40.0.0.1/24"`
Settings for VM networking have to be enabled just on the first VM host
**_NOTE:_** If you have multiple deployments in your network then it is recommended to change `vxlan id` and `vxlan_gw_ip`.

```
dhcp:
  - 120
vxlan_gw_ip: "40.0.0.1/24"
```

vm_hashed_passwd parameter is used to configure password for root user inside VMs
Default value is just placeholder, which needs to be changed to real hashed password before deployment.
To create hashed password use e.g.: openssl passwd -6 -salt SaltSalt <your_password>

```
vm_hashed_passwd: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

vxlan_device parameter specify network interface, which will be used to setup vxlan network.
It has to be interface connected to physical network, which is available on all VM hosts.
Interface has to have IP address assigned on all VM hosts from the same IP subnet.

```
vxlan_device: eno2
```

cpu_host_os is optional parameter, which changes default number of CPUs reserved for VM host OS.
Parameter is commented out by default, which means that default value 16 is used. Assigned value have to be even. The lowest value can be 2.

```
#cpu_host_os: 8
```


Next section provides definition of VMs, which will be created during deployment process and which will be used as control and worker nodes there.

vms option defines the list of VMs. Each VM is defined by following parameters:
`type` defines type of VM and following types are supported: "ctrl" and "work"
`name` defines hostname for the VM, which is assigned to VM. That name have to be used for corresponding host_vars file. e.g.: host_vars/vm-work-1.yml
`cpu_total` defines total number of CPUs assigned to VM. If value `0` is added here then all available CPUs from one NUMA node are assigned to this VM.
            If value `0` is added together with optional parameter `alloc_all: true` then all available CPUs from VM host are assigned to this VM.
`memory` defines amount of memory assigned to VM in MB
`vxlan` defines vxlan id of the vxlan network, where VM will be connected to. It has to be the one, which was added to dhcp parameter above.

`pci` defines list of PCI devices assigned to VM. It contains PCI ids for SRIOV NIC VFs and SRIOV QAT VFs which are assigned to VM. The list can be empty as well. PCI section is relevant only for VM type `work`. In example configuration bellow we've assigned 4 NIC VFs and 2 QAT VFs.

To be able to configure PCI ids for VFs we need to know their "naming convention". We need to connect to VM host and check PCI ids for VFs there.
**For SRIOV NIC VFs:**  
To check if VFs exist there run following command:  
for the first PF interface 18:00.0 from `dataplane_interfaces` above:
```
cat /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface 18:00.1 from `dataplane_interfaces` above:
```
cat /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs
```
If the commands return "0" then there are no VFs created there and we need to create them temporary.  
To create them you need to run following command:  
for the first PF interface 18:00.0 from `dataplane_interfaces` above:
```
echo "8" > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface 18:00.1 from `dataplane_interfaces` above:
```
echo "2" > /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs
```
Number used in those command is number of VFs to be created and it was taken from interface configuration above. Nevertheless we can use higher number as well to see naming convention.

Now we can check number of created VFs using cat command as before:
for the first PF interface 18:00.0 from `dataplane_interfaces` above:
```
cat /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface 18:00.1 from `dataplane_interfaces` above:
```
cat /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs
```
The commands return number of created VFs. It should be the same number as number used in echo command above.  
**_NOTE:_** for some drivers the received number of created VFs can be limited to "max number of VFs"

To see PCI ids for NICs and created VFs run following command:
```
lspci |grep -i Ether
```

```
18:00.0 Ethernet controller: Intel Corporation Ethernet Controller XXV710 for 25GbE SFP28 (rev 02)
18:00.1 Ethernet controller: Intel Corporation Ethernet Controller XXV710 for 25GbE SFP28 (rev 02)
18:02.0 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:02.1 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:02.2 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:02.3 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:02.4 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:02.5 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:02.6 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:02.7 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:0a.0 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
18:0a.1 Ethernet controller: Intel Corporation Ethernet Virtual Function 700 Series (rev 02)
```

The first 8 VFs belongs to PF 18:00.0 and the next 2 VFs belongs to PF 18:00.1
Select PCI ids for VFs to be assigned to VM. In example configuration bellow we've selected 18:02.2, 18:02.3, 18:02.4 and 18:02.5


If we created VFs in steps above then we can delete them again via following command:  
for the first PF interface 18:00.0 from `dataplane_interfaces` above:
```
echo "0" > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface 18:00.1 from `dataplane_interfaces` above:
```
echo "0" > /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs
```

**For SRIOV QAT VFs:**  
To check if VFs exist there run following command:  
for the first PF device 0000:3d:00.0 from `qat_devices` above. For other PF devices use the same commands with updated PCI id and VF number.
```
cat /sys/bus/pci/devices/0000\:3d\:00.0/sriov_numvfs
```

If the commands return "0" then there are no VFs created there and we need to create them temporary.  
To create them you need to run following command:
```
echo "12" > /sys/bus/pci/devices/0000\:3d\:00.0/sriov_numvfs
```

Number used in this command is number of VFs to be created and it was taken from `qat_devices` configuration above. Nevertheless we can use higher number as well to see naming convention.

Now we can check number of created VFs using cat command as before:
```
cat /sys/bus/pci/devices/0000\:3d\:00.0/sriov_numvfs
```

The commands return number of created VFs. It should be the same number as number used in echo command above.  
**_NOTE:_** for some drivers the received number of created VFs can be limited to "max number of VFs"

To see PCI ids for QAT devices run following command:
```
lspci -nn |grep -i Quick
```

```
3d:00.0 Co-processor [0b40]: Intel Corporation C62x Chipset QuickAssist Technology [8086:37c8] (rev 04)
3f:00.0 Co-processor [0b40]: Intel Corporation C62x Chipset QuickAssist Technology [8086:37c8] (rev 04)
da:00.0 Co-processor [0b40]: Intel Corporation C62x Chipset QuickAssist Technology [8086:37c8] (rev 04)
```

To see PCI ids for created QAT VFs run following command:  
Device id string to grep is taken from square brackets above. We search for that device is and "device id + 1", which corresponds to VFs
```
lspci -nn |grep -i "37c[89]"
```

```
3d:00.0 Co-processor [0b40]: Intel Corporation C62x Chipset QuickAssist Technology [8086:37c8] (rev 04)
3d:01.0 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:01.1 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:01.2 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:01.3 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:01.4 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:01.5 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:01.6 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:01.7 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.0 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.1 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.2 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.3 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.4 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.5 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.6 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3d:02.7 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:00.0 Co-processor [0b40]: Intel Corporation C62x Chipset QuickAssist Technology [8086:37c8] (rev 04)
3f:01.0 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:01.1 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:01.2 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:01.3 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:01.4 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:01.5 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:01.6 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:01.7 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:02.0 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:02.1 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:02.2 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:02.3 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:02.4 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
3f:02.5 Co-processor [0b40]: Intel Corporation Device [8086:37c9] (rev 04)
...
```

There are 16 VFs created for each QAT PF device  
Select PCI ids for VFs to be assigned to VM. In example configuration bellow we've selected 3d:02.3 and 3f:02.3


If we created VFs in steps above then we can delete them again via following command:
```
echo "0" > /sys/bus/pci/devices/0000\:3d\:00.0/sriov_numvfs
```

Following optional parameters should be used by experts only:
`numa` defines NUMA node from which cores will be selected automatically or from which we have selected the cores manually in "expert mode".
       In expert mode example bellow: For vm-ctrl-1 it means NUMA node0. For vm-work-1 it means NUMA node1.
`cpus` defines, which cpus from the vm-host will be assigned to that VM

To be able to configure it, we need to get cpu info from target vm-host, where we run `lscpu` command. Following lines from output are relevant for it:

```
lscpu
CPU(s):                          112
On-line CPU(s) list:             0-111
Thread(s) per core:              2
Core(s) per socket:              28
Socket(s):                       2
NUMA node(s):                    2
NUMA node0 CPU(s):               0-27,56-83
NUMA node1 CPU(s):               28-55,84-111
```

In current case we have machine with 112 CPUs. It has 2 sockets with 28 cores. Each core has two threads. It has 2 NUMA nodes one per socket.
The first few cores from NUMA node0 we reserve for system. By default it is 8. It means 16 CPUs. Specifically CPUs 0-7 (the first threads from selected cores) and CPUs 56-63 (the corresponding second threads from selected cores)
If we want to assign 8 CPUs to vm-ctrl-1 then we can select next 4 cores, which means CPUs 8-11 and 64-67. We need to ensure that all CPUs comes from single NUMA node.
If we want to assign 16 CPUs to vm-work-1 then we can select next 8 cores from NUMA node0 or select 8 cores from NUMA node1. In expert mode example configuration below we've selected 8 cores from NUMA node1, which means CPUs 28-35 and 84-91.

`emu_cpus` parameter is DEPRECATED and should not be used. If it is used then it is ignored and has no effect. Emulators CPUs are picked-up automatically. The first CPU and the first CPU thread are taken.

`alloc_all` parameter defines if all available CPUs from VM host will be assigned to current VM. Default value is `false`, which means that all unallocated CPUs from single NUMA node will be assigned to current VM. If we set parameter value to `true` then NUMA allignment is switched off and all available CPUs from all NUMA nodes on VM host will be assigned to current VM. The alloc_all parameter is used only when 'cpu_total' parameter value is set to '0'
That option was added to enable full CPU utilization on VM host during performance tests.


Example configuration contains 2 VMs, 1 control and 1 work node. We've tested configuration with 5 VMs, 3 control and 2 work nodes

```
vms:
  - type: "ctrl"
    name: "vm-ctrl-1"
    cpu_total: 8
    memory: 20480
    vxlan: 120
  - type: "work"
    name: "vm-work-1"
    cpu_total: 16
    memory: 61440
    vxlan: 120
    pci:
      - "18:02.2"
      - "18:02.3"
      - "18:02.4"
      - "18:02.5"
      - "3d:02.3"
      - "3f:02.3"

```

Example expert mode configuration contains 2 VMs, 1 control and 1 work node.

```
vms:
  - type: "ctrl"
    name: "vm-ctrl-1"
    cpus: "8-11,64-67"
    numa: 0
    cpu_total: 8
    memory: 20480
    vxlan: 120
  - type: "work"
    name: "vm-work-1"
    cpus: "28-35,84-91"
    numa: 1
    cpu_total: 16
    memory: 61440
    vxlan: 120
    pci:
      - "18:02.2"
      - "18:02.3"
      - "18:02.4"
      - "18:02.5"
      - "3d:02.3"
      - "3f:02.3"

```

In case of multi node setup we need to create host_vars file for each VM host and properly configure VMs which will be created on that VM host.
VM names have to be unique across all VM hosts.
**_NOTE:_** If you start more deployments from the same ansible host then you have to ensure that VM names are unique even across all deployments. Each deployment should have unique vxlan id and vxlan_gw_ip to ensure that they are independent.
**_NOTE:_** If the same VM name is used then ssh config is overwritten. It causes that original VM (the one, which was created first) become unreachable.



## Worker node specific options

There's also a set of configuration options that are applied in per-node manner in current case for VM type `work`.

The first set of variables configure assigned SRIOV NIC VFs and SRIOV QAT VFs inside VM. It requires setting `iommu_enabled` as `false`.

**For SRIOV NIC** it requires passing names of interfaces together with additional NIC parameters. In below example `dataplane_interfaces` configuration contains 4 interfaces, where the first one starting with bus_info "06:00.0". The number in PCI id is sequentially increasing. `sriov_numvfs` must be "0" here. We can't create new VFs out of provided VF.
`pf_driver` and `default_vf_driver` are not use at the moment. All interfaces are assigned to kernel mode iavf driver inside VM.
The number of interfaces defined here in `dataplane_interfaces` have to be the same as number of NIC VFs assigned to this VM !
In our example configuration we've assigned 4 NIC VFs, so we have 4 interfaces defined here.

**For SRIOV QAT** it requires passing qat id of QAT device. `qat_sriov_numvfs` must be "0" here. We can't create new VFs out of provided VF. In below example `qat_devices` configuration contains 2 QAT devices. `qat_id` continue in numbering from `dataplane_interfaces`. The last bus_info there was `"09:00:0"` so, the first qat_id will be `"0000:0a:00.0"`.
The number of QAT devices defined here in `qat_devices` has to be the same as number of QAT VFs assigned to this VM!
In our example configuration we've assigned 2 QAT VFs, so we have 2 devices defined here.

This setting will add `vfio-pci.disable_denylist=1` kernel flags for kernel >=5.9 or specific RHEL/CentOS versions, and as a result will reboot the target vm-work VM during deployment.
```
dataplane_interfaces:
  - bus_info: "06:00.0"
    pf_driver: iavf
    sriov_numvfs: 0
    default_vf_driver: "igb_uio"
  - bus_info: "07:00.0"
    pf_driver: iavf
    sriov_numvfs: 0
    default_vf_driver: "vfio-pci"
  - bus_info: "08:00.0"
    pf_driver: vfio-pci
    sriov_numvfs: 0
    default_vf_driver: "vfio-pci"
  - bus_info: "09:00.0"
    pf_driver: iavf
    sriov_numvfs: 0
    default_vf_driver: "igb_uio"


qat_devices:
  - qat_id: "0000:0a:00.0"
    qat_sriov_numvfs: 0

  - qat_id: "0000:0b:00.0"
    qat_sriov_numvfs: 0

```

**For SGX** currently it's in experimental phase - it's compiling libvirt from custom repository. Beacause of that it's not supported on all operating system, but only for: Ubuntu 22.04 for host and Ubuntu 20.04 for VMs.

### Once the deployment is finished we can access VMs from ansible_host via VM name:
```
ssh vm-ctrl-1
ssh vm-work-1
```
