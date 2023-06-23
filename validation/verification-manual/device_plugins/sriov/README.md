# SR-IOV Network Device Plugin
This example shows how to use the SR-IOV Network Device Plugin for assigning additional Virtual Functions (VFs) to workloads in Kubernetes. The test for verifying Kernel bound devices also uses the SR-IOV CNI Plugin to provide IPAM functionality that assigns IP addresses to the additional VFs or interfaces in the workload.

## Prerequisites for VMRA
With the current deployment, all SR-IOV VFs are initially be assigned to the iavf driver. As a result, they will be listed as netdevice resources as shown below:
```
# kubectl get node vm-work-1 -o json | jq '.status.allocatable'
{
  "cpu": "13",
  "ephemeral-storage": "239597877261",
  "hugepages-1Gi": "4Gi",
  "intel.com/intel_sriov_netdevice": "4",
  "memory": "56650408Ki",
  "pods": "110",
}
```
To reassign VFs to a DPDK driver, use the `dpdk-devbind.py` script available on all worker nodes where DPDK is installed:
1. List the available VFs on the worker node where you want to modify the driver assignment
```
# dpdk-devbind.py
Network devices using kernel driver
===================================
0000:01:00.0 'Virtio network device 1041' if=enp1s0 drv=virtio-pci unused=igb_uio,vfio-pci *Active*
0000:04:00.0 'Ethernet Virtual Function 700 Series 154c' if=enp4s0 drv=iavf unused=igb_uio,vfio-pci
0000:05:00.0 'Ethernet Virtual Function 700 Series 154c' if=enp5s0 drv=iavf unused=igb_uio,vfio-pci
0000:06:00.0 'Ethernet Virtual Function 700 Series 154c' if=enp6s0 drv=iavf unused=igb_uio,vfio-pci
0000:07:00.0 'Ethernet Virtual Function 700 Series 154c' if=enp7s0 drv=iavf unused=igb_uio,vfio-pci
```
2. Rebind VFs to the vfio-pci driver:
```
# dpdk-devbind.py -b vfio-pci 04:00.0 05:00.0
```
3. On a controller node, find and delete the SR-IOV Device Plugin pods, which will then be recreated:
```
# kubectl get pods -A | grep sriov
kube-system    sriov-net-dp-kube-sriov-device-plugin-amd64-knlqw       1/1     Running		0	168m
```
```
# kubectl delete pod sriov-net-dp-kube-sriov-device-plugin-amd64-knlqw -n kube-system
```

## Verify Node Resources
Start by listing allocatable node resources for the target worker node:
```
# kubectl get node <worker node> -o json | jq '.status.allocatable'
{
  "cpu": "95550m",
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
In the above, there are three SR-IOV network device plugin resources: `intel.com/intel_sriov_dpdk_700_series`, `intel.com/intel_sriov_dpdk_800_series` and `intel.com/intel_sriov_netdevice`. The netdevice VFs are bound to a kernel driver and can be configured using the SR-IOV CNI Plugin. The dpdk VFs are bound to a DPDK driver, which allows an application to operate in userspace, bypassing the kernel network stack for ultra-high performance.

For the Kernel bound test where the SR-IOV CNI plugin is used, verify that the example network attachment definition is available:
```
# kubectl get net-attach-def –all-namespaces
NAME               AGE 
sriov-net          3d23h
```
Also check that the `sriov-net` net-attach-def uses the `intel.com/intel_sriov_netdevice` resource:
```
# kubectl describe net-attach-def sriov-net | grep Annotations 
Annotations:  k8s.v1.cni.cncf.io/resourceName: intel.com/intel_sriov_netdevice
```

## Verifying DPDK Devices
For this test we will verify the VFs bound to the DPDK driver, such as `intel.com/intel_sriov_dpdk_700_series` and `intel.com/intel_sriov_dpdk_800_series`.

### Deploy Workload
To test the SR-IOV Network Device Plugin, the provided pod manifest [pod-sriov-dpdk.yml](pod-sriov-dpdk.yml) can be used. The content of the file is:
```
---
apiVersion: v1  
kind: Pod
metadata:
  name: pod-sriov-dpdk-1
spec:
  containers:
  - name: pod-sriov-dpdk-1
    image: ubuntu:focal
    command: [ "/bin/bash", "-c" ]
    args: [ "sleep inf" ]
    resources:
      requests:
        intel.com/intel_sriov_dpdk_700_series: '1'
      limits:
        intel.com/intel_sriov_dpdk_700_series: '1'
```
Note the `intel.com/intel_sriov_dpdk_700_series` resource name, and make sure the resource matches that of the worker node(s) in the cluster. 

Now deploy the pod:
```
# kubectl apply -f pod-sriov-dpdk.yml
```

### Verify Pod Resources
Once running, verify that the SR-IOV device is available in the pod:
```
# kubectl exec pod-sriov-dpdk-1 -- env | grep PCIDEVICE 
PCIDEVICE_INTEL_COM_INTEL_SRIOV_DPDK_700_SERIES=0000:86:02.1
```
Note that the name of the resource(s) depends on the request in the pod manifest. If several devices of the same type are requested they will show up as comma separated values, e.g. `0000:86:02.1,0000:86:02.2`.

## Verifying Kernel Devices
For this test we will verify the VFs bound to the kernel driver, available as `intel.com/intel_sriov_netdevice`. This test also uses the SR-IOV CNI Plugin to assign IP addresses to the VFs.

### Deploy Workload
To test the SR-IOV Network Device Plugin, the provided pod manifest [pod-sriov-netdevice.yml](pod-sriov-netdevice.yml) can be used. The content of the file is:
```
---
apiVersion: v1  
kind: Pod
metadata:
  name: pod-sriov-netdevice-1
  annotations:
    k8s.v1.cni.cncf.io/networks: sriov-net
spec:
  containers:
  - name: pod-sriov-netdevice-1
    image: ubuntu:focal
    command: [ "/bin/bash", "-c" ]
    args:
      - apt update;
        apt install -y iproute2;
        sleep inf
    resources:
      requests:
        intel.com/intel_sriov_netdevice: '1'
      limits:
        intel.com/intel_sriov_netdevice: '1'
```
This pod requests a `intel.com/intel_sriov_netdevice` device resource from the SR-IOV Device Plugin, and also the additional functionality provided by the SR-IOV CNI Plugin through the annotation `k8s.v1.cni.cncf.io/networks: sriov-net`.

Deploy the pod:
```
# kubectl apply -f pod-sriov-netdevice.yml
```

### Verify Pod Resources
Once running, verify that the SR-IOV device is available in the pod:
```
# kubectl exec pod-sriov-netdevice-1 -- env | grep PCIDEVICE 
PCIDEVICE_INTEL_COM_INTEL_SRIOV_NETDEVICE=0000:86:0a.1
```

After waiting for the iproute2 package to be installed, also verify that the SR-IOV CNI Plugin has made the device available as an interface with an IP address assigned:
```
# kubectl exec pod-sriov-netdevice-1 -- ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
3: eth0@if69: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP group default
    link/ether c6:0d:c3:a5:57:15 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.244.1.26/24 brd 10.244.1.255 scope global eth0
       valid_lft forever preferred_lft forever
16: net1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 7e:ad:44:41:91:e5 brd ff:ff:ff:ff:ff:ff
    inet 10.56.217.172/24 brd 10.56.217.255 scope global net1
       valid_lft forever preferred_lft forever
```
The `net1` interface is the one added through the SR-IOV Device Plugin and configured throug the SR-IOV CNI Plugin.
