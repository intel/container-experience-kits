# Check DDP Profiles
These steps show how to check Intel Dynamic Device Personalization (DDP) Profiles on a system. DDP provides dynamic reconfiguration of the packet processing pipeline for specific use cases.

To assist with checking and verifying that DDP profiles are loaded, `ddptool` will be used. This can be downloaded from [https://github.com/intel/ddp-tool/tree/1.0.17.0].

## Build ddptool
To build `ddptool`, run the following commands on each worker node with DDP Profiles configured:
```
# git clone https://github.com/intel/ddp-tool.git
# cd ddp-tool
# git checkout 1.0.17.0
# make
```

## Check DDP Profiles in Intel Ethernet 700 Series Network Adapters
To verify that the correct DDP profile was loaded, use the following command:
```
# sudo ./ddptool -a
Intel(R) Dynamic Device Personalization Tool
DDPTool version 1.0.17.0
Copyright (C) 2019 - 2021 Intel Corporation.

NIC  DevId D:B:S.F      DevName         TrackId  Version      Name
==== ===== ============ =============== ======== ============ ==============================
001) 158B  0000:18:00.0 ens785f0        80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
002) 158B  0000:18:00.1 ens785f1        80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
003) 154C  0000:18:02.0 ens785f0v0      80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
004) 154C  0000:18:02.1 ens785f0v1      80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
005) 154C  0000:18:02.2 ens785f0v2      80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
006) 154C  0000:18:02.3 ens785f0v3      80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
007) 154C  0000:18:02.4 ens785f0v4      80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
008) 154C  0000:18:02.5 ens785f0v5      80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
009) 154C  0000:18:0A.0 N/A             80000008 1.0.3.0      GTPv1-C/U IPv4/IPv6 payload   
010) 154C  0000:18:0A.1 N/A             -        -                                          
011) 154C  0000:18:0A.2 N/A             -        -                                          
012) 154C  0000:18:0A.3 N/A             -        -                                          
013) 1592  0000:AF:00.0 ens801f0        -        -            -                             
014) 1592  0000:AF:00.1 ens801f1        -        -            -                             
```

## Check DDP Profiles in Intel Ethernet 800 Series Network Adapters 
To verify that the correct DDP profile was loaded, use the following command:
```
# sudo ./ddptool -a
Intel(R) Dynamic Device Personalization Tool
DDPTool version 1.0.17.0
Copyright (C) 2019 - 2021 Intel Corporation.

NIC  DevId D:B:S.F      DevName         TrackId  Version      Name
==== ===== ============ =============== ======== ============ ==============================
001) 1592  0000:B1:00.0 ens801f0        C0000002 1.3.35.0     ICE COMMS Package             
002) 1592  0000:B1:00.1 ens801f1        C0000002 1.3.35.0     ICE COMMS Package             
003) 1889  0000:B1:01.0 ens801f0v0      C0000002 1.3.35.0     ICE COMMS Package             
004) 1889  0000:B1:01.1 ens801f0v1      C0000002 1.3.35.0     ICE COMMS Package             
005) 1889  0000:B1:01.2 ens801f0v2      C0000002 1.3.35.0     ICE COMMS Package             
006) 1889  0000:B1:01.3 ens801f0v3      C0000002 1.3.35.0     ICE COMMS Package             
007) 1889  0000:B1:01.4 ens801f0v4      C0000002 1.3.35.0     ICE COMMS Package             
008) 1889  0000:B1:01.5 ens801f0v5      C0000002 1.3.35.0     ICE COMMS Package             
009) 1889  0000:B1:11.0 N/A             C0000002 1.3.35.0     ICE COMMS Package             
010) 1889  0000:B1:11.1 N/A             -        -                                          
011) 1889  0000:B1:11.2 N/A             -        -                                          
012) 1889  0000:B1:11.3 N/A             -        -                                          
```

## Check SR-IOV Resources
To verify that SR-IOV network resources are present, use the following command from a controller node:
```
# kubectl get node <worker node> -o json | jq '.status.allocatable'
{
  "cpu": "93",
  "ephemeral-storage": "452220352993",
  "hugepages-1Gi": "4Gi",
  "hugepages-2Mi": "256Mi",
  "intel.com/intel_sriov_dpdk_700_series": "2",
  "intel.com/intel_sriov_dpdk_800_series": "2",
  "intel.com/intel_sriov_netdevice": "4",
  "memory": "191733164Ki",
  "pods": "110",
  "qat.intel.com/generic": "32"
}
```
The relevant network resources above are: `intel.com/intel_sriov_dpdk_700_series`, `intel.com/intel_sriov_dpdk_800_series` and `intel.com/intel_sriov_netdevice`.
