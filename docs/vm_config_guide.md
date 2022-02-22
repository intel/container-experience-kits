# VM specific configuration for SRIOV NIC and SRIOV QAT


In order to deploy VM case, VM specific configuration has to be used. It is generated automatically via `make`. It is generated into `examples/vm/` directory. Configurations for each profile are kept in profile named directories. Group vars for VM case have set `vm_enabled` value to `true`. To deploy standard BM RA the configuration files must be re-generated. It is not sufficient to change the value of `vm_enabled` to `false`.

```
vm_enabled: true
```


## vm-host specific options

There's also a set of configuration options that are applied in per-node manner.

First set of variables enables SRIOV for selected network adapters and QAT devices. It requires setting `iommu_enabled` as `true`.

**For SRIOV NIC** it requires passing names of the physical function interfaces together with additional NIC parameters, which contain also an option to define how many virtual functions should be created for each physical function. In below example `dataplane_interfaces` configuration will create 8 VFs for `enp24s0f0` PF interface and attach them to kernel mode `iavf` driver by default and listed vfs (vf_00 and vf_05) attach to selected driver (in our case `vfio-pci` driver). Then it will create 2 VFs for `enp24s0f1` PF interface and attach them to `vfio-pci` driver.

**For SRIOV QAT** it requires passing qat id of the QAT physical function together with an option to define how many virtual functions should be created for each physical function. In below example `qat_devices` configuration will create 12 VFs for `"0000:3d:00.0"` PF device, 10 VFs for `"0000:3f:00.0"` PF device and 10 VFs for `"0000:da:00.0"` PF device.  
**_NOTE:_** Some QAT drivers ignore requested number of VFs and create maximum number of VFs allowed by current QAT device. Where: "0" means no VFs, number between "1" and "max num of VFs" creates max number of VFs and number above "max num of VFs" cause an error.

This setting will also add IOMMU kernel flags, and as a result will reboot the target vm-host during deployment.
```
dataplane_interfaces:
  - name: enp24s0f0
    bus_info: "18:00.0"
    pf_driver: i40e
    ddp_profile: "gtp.pkgo"
    default_vf_driver: "iavf"
    sriov_numvfs: 8
    sriov_vfs:
      vf_00: "vfio-pci"
      vf_05: "vfio-pci"

  - name: enp24s0f1
    bus_info: "18:00.1"
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

Next section provides definition of VMs, which will be created during deployment process and which will be used as control and worker nodes there.
The first option defines version of Ubuntu cloud image, which will be used inside VMs. Currently supported versions are: "20.04" and "21.04"
```
vm_image_version: "21.04"`
```

The second option defines the list of VMs. Each VM is defined by following parameters:  
`type` defines type of VM and following types are supported: "ctrl" and "work"  
`name` defines hostname for the VM, which is assigned to VM. That name have to be used for corresponding host_vars file. e.g.: host_vars/vm-work-1.yml  
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
The first few cores from NUMA node0 we reserve for system. In our case 8. It means 16 CPUs. Specifically CPUs 0-7 (the first threads from selected cores) and CPUs 56-63 (the corresponding second threads from selected cores)
If we want to assign 8 CPUs to vm-ctrl-1 then we can select next 4 cores, which means CPUs 8-11 and 64-67. We need to ensure that all CPUs comes from single NUMA node.
If we want to assign 16 CPUs to vm-work-1 then we can select next 8 cores from NUMA node0 or select 8 cores from NUMA node1. In example configuration bellow we've selected 8 cores from NUMA node1, which means CPUs 28-35 and 84-91.

`emu_cpus` defines, which CPUs from CPUs listed in `cpus` will be used for emulator. We select the first assigned core, which means for vm-ctrl-1 CPUs 8 and 64. For vm-work-1 it means CPUs 28 and 84  
`numa` defines NUMA node from which we have selected the cores. For vm-ctrl-1 it means NUMA node0. For vm-work-1 it means NUMA node1.  
`cpu_total` defines total number of CPUs assigned to VM  
`memory` defines amount of memory assigned to VM in MB  
`pci` defines list of PCI devices assigned to VM. It contains PCI ids for SRIOV NIC VFs and SRIOV QAT VFs which are assigned to VM. The list can be empty as well. PCI section is relevant only for VM type `work`. In example configuration bellow we've assigned 4 NIC VFs and 2 QAT VFs.

To be able to configure PCI ids for VFs we need to know their "naming convention". We need to connect to vm-host and check PCI ids for VFs there.  
**For SRIOV NIC VFs:**  
To check if VFs exist there run following command:  
for the first PF interface enp24s0f0 from `dataplane_interfaces` above:
```
cat /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface enp24s0f1 from `dataplane_interfaces` above:
```
cat /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs
```
If the commands return "0" then there are no VFs created there and we need to create them temporary.  
To create them you need to run following command:  
for the first PF interface enp24s0f0 from `dataplane_interfaces` above:
```
echo "8" > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface enp24s0f1 from `dataplane_interfaces` above:
```
echo "2" > /sys/bus/pci/devices/0000\:18\:00.1/sriov_numvfs
```
Number used in those command is number of VFs to be created and it was taken from interface configuration above. Nevertheless we can use higher number as well to see naming convention.

Now we can check number of created VFs using cat command as before:
for the first PF interface enp24s0f0 from `dataplane_interfaces` above:
```
cat /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface enp24s0f1 from `dataplane_interfaces` above:
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
for the first PF interface enp24s0f0 from `dataplane_interfaces` above:
```
echo "0" > /sys/bus/pci/devices/0000\:18\:00.0/sriov_numvfs
```

for the second PF interface enp24s0f1 from `dataplane_interfaces` above:
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
**_NOTE:_** for some drivers the received number of created VFs can be limited to "nax number of VFs"

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


Example configuration contains 2 VMs, 1 control and 1 work node. We've tested configuration with 5 VMs, 3 control and 2 work nodes

```
vms:
  - type: "ctrl"
    name: "vm-ctrl-1"
    cpus: "8-11,64-67"
    emu_cpus: "8,64"
    numa: 0
    cpu_total: 8
    memory: 20480
  - type: "work"
    name: "vm-work-1"
    cpus: "28-35,84-91"
    emu_cpus: "28,84"
    numa: 1
    cpu_total: 16
    memory: 61440
    pci:
      - "18:02.2"
      - "18:02.3"
      - "18:02.4"
      - "18:02.5"
      - "3d:02.3"
      - "3f:02.3"

```


## Worker node specific options

There's also a set of configuration options that are applied in per-node manner in current case for VM type `work`.

The first set of variables configure assigned SRIOV NIC VFs and SRIOV QAT VFs inside VM. It requires setting `iommu_enabled` as `false`.

**For SRIOV NIC** it requires passing names of interfaces together with additional NIC parameters. In below example `dataplane_interfaces` configuration contains 4 interfaces, where the first one starting with name enp4s0 and bus_info "04:00.0". Last number in name and PCI id is sequentially increasing. `sriov_numvfs` must be "0" here. We can't create new VFs out of provided VF.
`pf_driver` and `default_vf_driver` are not use at the moment. All interfaces are assigned to kernel mode iavf driver inside VM.  
The number of interfaces defined here in `dataplane_interfaces` have to be the same as number of NIC VFs assigned to this VM !  
In our example configuration we've assigned 4 NIC VFs, so we have 4 interfaces defined here.

**For SRIOV QAT** it requires passing qat id of QAT device. `qat_sriov_numvfs` must be "0" here. We can't create new VFs out of provided VF. In below example `qat_devices` configuration contains 2 QAT devices. `qat_id` continue in numbering from `dataplane_interfaces`. The last bus_info there was `"07:00:0"` so, the first qat_id will be `"0000:08:00.0"`.  
The number of QAT devices defined here in `qat_devices` has to be the same as number of QAT VFs assigned to this VM!  
In our example configuration we've assigned 2 QAT VFs, so we have 2 devices defined here.

This setting will add `vfio-pci.disable_denylist=1` kernel flags for kernel >=5.9 or specific RHEL/CentOS versions, and as a result will reboot the target vm-work VM during deployment.
```
dataplane_interfaces:
  - name: enp4s0
    bus_info: "04:00.0"
    pf_driver: iavf
    sriov_numvfs: 0
    default_vf_driver: "igb_uio"
  - name: enp5s0
    bus_info: "05:00.0"
    pf_driver: iavf
    sriov_numvfs: 0
    default_vf_driver: "igb_uio"
  - name: enp6s0
    bus_info: "06:00.0"
    pf_driver: iavf
    sriov_numvfs: 0
    default_vf_driver: "vfio-pci"
  - name: enp7s0
    bus_info: "07:00.0"
    pf_driver: vfio-pci
    sriov_numvfs: 0
    default_vf_driver: "vfio-pci"


qat_devices:
  - qat_id: "0000:08:00.0"
    qat_sriov_numvfs: 0

  - qat_id: "0000:09:00.0"
    qat_sriov_numvfs: 0

```

### Once the deployment is finished we can access VMs from ansible_host via VM name:
```
ssh vm-ctrl-1
ssh vm-work-1
```
