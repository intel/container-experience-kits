# SR-IOV Network Operator
This example shows how to use the SR-IOV Network Operator for assigning Virtual Functions (VFs) to workloads in Kubernetes. The steps provided here will show how to verify node resources, find details for each of the SR-IOV resources, create a SriovNetwork resource providing IPAM and lastly how to use the resources when deploying a pod.

## Verify Node Resources
Start by listing allocatable node resources for the target worker node:
```
# kubectl get node <worker node> -o json | jq '.status.allocatable'
{
  "cpu": "95550m",
  "ephemeral-storage": "189274027310",
  "hugepages-1Gi": "4Gi",
  "hugepages-2Mi": "256Mi",
  "intel.com/ens785_intelnics_1": "4",
  "intel.com/ens786_intelnics_1": "4",
  "intel.com/ens801_intelnics_1": "4",
  "intel.com/ens802_intelnics_1": "4",
  "memory": "518549664Ki",
  "pods": "110",
}
```
In the above, the resources `"intel.com/*"` are all created through the SR-IOV Network Operator, based on the configuration of `dataplane_interfaces` in `host_vars/<worker node>.yml`. Based on the name of the interfaces (e.g `ens785`) it can be difficult to see what VF driver is being used, but below is an example of how to get this information.

## Find Resource Details
To get more details about each of the SR-IOV Network Operator resources, we can use the `SriovNetworkNodeState` resource deploying as part of the operator:
```
# kubectl get SriovNetworkNodeState <worker node> -n sriov-network-operator -o json | jq '.spec'
{
  "dpConfigVersion": "5941",
  "interfaces": [
    {
      "linkType": "eth",
      "mtu": 1500,
      "name": "ens785",
      "numVfs": 4,
      "pciAddress": "0000:4b:00.0",
      "vfGroups": [
        {
          "deviceType": "vfio-pci",
          "mtu": 1500,
          "policyName": "cypq-11-ens785-sriov-policy-1",
          "resourceName": "ens785_intelnics_1",
          "vfRange": "0-3"
        }
      ]
    },
    {
      "linkType": "eth",
      "mtu": 1500,
      "name": "ens786",
      "numVfs": 4,
      "pciAddress": "0000:31:00.0",
      "vfGroups": [
        {
          "deviceType": "netdevice",
          "mtu": 1500,
          "policyName": "cypq-11-ens786-sriov-policy-1",
          "resourceName": "ens786_intelnics_1",
          "vfRange": "0-3"
        }
      ]
    },
(...)
}
```
In the above output, we can see the `"pciAddress"` which is used when configuring the VFs in `host_vars`, the "`deviceType`" which indicates what VF driver is being used ("netdevice" is common for kernel drivers, e.g. "iavf"), and the "resourceName" which maps to the node resources listed previously.

## Create SR-IOV Resource with IPAM
After selecting one of the SR-IOV Network Operator node resources that use "netdevice", we can create a `SriovNetwork` resource that adds IPAM capabilities to the VFs. This is similar to what is provided through SR-IOV CNI, but using a different resource name.
The provided SriovNetwork manifest [sriov-network.yml](sriov-network.yml) can be used. The content of the file is:
```
---
apiVersion: sriovnetwork.openshift.io/v1
kind: SriovNetwork
metadata:
  name: sriov-netdev-ipam
  namespace: sriov-network-operator
spec:
  ipam: |
    {
      "type": "host-local",
      "subnet": "10.11.12.0/24",
      "rangeStart": "10.11.12.171",
      "rangeEnd": "10.11.12.181",
      "routes": [{
        "dst": "0.0.0.0/0"
      }],
      "gateway": "10.11.12.1"
    }
  networkNamespace: default
  resourceName: ens786_intelnics_1
```
Be sure to update `resourceName` to match a node resource with `"deviceType": "netdevice"`.
Deploy the resource using:
```
# kubectl apply -f sriov-network.yml
```
Once deployed, verify that it has been created using:
```
# kubectl get sriovnetwork -A
NAMESPACE                NAME                AGE
sriov-network-operator   sriov-netdev-ipam   10s
```

## Deploy Workloads
To use the SR-IOV Network Operator resources, we will deploy 2 different example pods. The first pod will use the `SriovNetwork` resource we created above, which provides a kernel interface with IPAM. The second pod will use one of the resources with `"deviceType": "vfio-pci"`, which can be used as a PCI device for DPDK inside the pod.

### Kernel Interface (netdevice)
For the first pod, the provided pod manifest [pod-sriov-netdevice.yml](pod-sriov-netdevice.yml) can be used. The content of the file is:
```
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-sriov-netdev-ipam
  annotations:
    k8s.v1.cni.cncf.io/networks: sriov-netdev-ipam
spec:
  containers:
  - name: pod-sriov-netdev-ipam
    image: ubuntu:focal
    imagePullPolicy: IfNotPresent
    command: [ "/bin/bash", "-c" ]
    args:
      - apt update;
        apt install -y net-tools;
        sleep inf
    resources:
      requests:
        intel.com/ens786_intelnics_1: '1'
      limits:
        intel.com/ens786_intelnics_1: '1'
```
Deploy the pod using:
```
# kubectl apply -f pod-sriov-netdevice.yml
```
Wait for the pod to start (and install net-tools), and check the interfaces:
```
# kubectl exec -it pod-sriov-netdev-ipam -- ifconfig
(...)
net1: flags=4099<UP,BROADCAST,MULTICAST>  mtu 1500
        inet 10.11.12.176  netmask 255.255.255.0  broadcast 10.11.12.255
        ether 8a:39:5f:e4:2c:0b  txqueuelen 1000  (Ethernet)
        RX packets 0  bytes 0 (0.0 B)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 0  bytes 0 (0.0 B)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```
As seen above, the SR-IOV interface has been added to the pod, and assigned an IP address throught the `SriovNetwork` IPAM configuration.

### PCI Interface (vfio-pci)
For this pod, once of SR-IOV Network Operator node resources using the vfio-pci driver will be used. From the previous steps, it can be seen that `"intel.com/ens785_intelnics_1"` is using vfio-pci, so this resource will be used to set up a pod. The provided pod manifest [pod-sriov-vfio-pci.yml](pod-sriov-vfio-pci.yml) can be used. The content of the file is:
```
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-sriov-vfio-pci
spec:
  containers:
  - name: pod-sriov-vfio-pci
    image: ubuntu:focal
    imagePullPolicy: IfNotPresent
    command: [ "/bin/bash", "-c" ]
    args: [ "sleep inf" ]
    resources:
      requests:
        intel.com/ens785_intelnics_1: '1'
      limits:
        intel.com/ens785_intelnics_1: '1'
```
Deploy the pod using:
```
# kubectl apply -f pod-sriov-vfio-pci.yml
```
Wait for the pod to start and then check the environment for the assigned vfio-pci VF:
```
# kubectl exec -it pod-sriov-vfio-pci -- env | grep PCIDEVICE
PCIDEVICE_INTEL_COM_ENS785_INTELNICS_1=0000:4b:01.3
```
The vfio-pci PCI device is listed in the environment, and is ready for use.
