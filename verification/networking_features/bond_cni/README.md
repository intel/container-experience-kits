# Bond CNI Plugin
This example shows how to use the Bond CNI Plugin to add a bonded interface to pods in Kubernetes.

The Bond CNI Plugin relies on other CNI Plugins to provide the interfaces to be used for the bond. Multus CNI Plugin adds support for multiple interfaces in a pod, SR-IOV Device Plugin makes Virtual Function (VF) resources available in Kubernetes, and the SR-IOV CNI Plugin configures the Virtual Functions (VFs) that are added to the pod.

## Configure Networks
Start by verifying that the Bond CNI Plugin is available on the worker nodes by connecting through SSH and checking that the Bond CNI binary is available:
```
# ll /opt/cni/bin/bond
-rwxr-xr-x. 1 root root 3836352 Feb 27 13:03 /opt/cni/bin/bond
```

Verify that VFs using the kernel driver are available on the worker nodes in the Kubernetes cluster:
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
Make sure to update `<worker node>` with the actual name of the worker node. The relevant resource above is `intel.com/intel_sriov_netdevice`.

Create a network attachment definintion that uses the resource. The provided manifest [sriov-bond-net.yml](sriov-bond-net.yml) can be used. The content of the file is:
```
---
apiVersion: "k8s.cni.cncf.io/v1" 
kind: NetworkAttachmentDefinition
metadata:
  name: sriov-bond-net
  annotations:
    k8s.v1.cni.cncf.io/resourceName: intel.com/intel_sriov_netdevice
spec:
  config: '{
  "type": "sriov",
  "name": "sriov-network",
  "spoofchk":"off"
}'
```
Deploy the network:
```
# kubectl apply -f sriov-bond-net.yml
```

Create a network attachment definition for Bond CNI that defines how the bond should be configured in the pod. The provided manifest [bond-net.yml](bond-net.yml) can be used. The content of the file is:
```
---
apiVersion: "k8s.cni.cncf.io/v1" 
kind: NetworkAttachmentDefinition
metadata:
  name: bond-net
spec:
  config: '{
  "type": "bond",
  "cniVersion": "0.3.1",
  "name": "bond-net",
  "ifname": "bond0",
  "mode": "active-backup",
  "failOverMac": 1,
  "linksInContainer": true,
  "miimon": "100",
  "links": [
     {"name": "net1"},
     {"name": "net2"}
  ],
  "ipam": {
    "type": "host-local",
    "subnet": "10.56.217.0/24",
    "routes": [{
      "dst": "0.0.0.0/0"
    }],
    "gateway": "10.56.217.1"
  }
}'
```
Deploy the network:
```
# kubectl apply -f bond-net.yml
```

Verify that both networks are available:
```
# kubectl get net-attach-def 
NAME             AGE 
bond-net         15s
sriov-bond-net   36s
```

## Deploy Workload
With the two network attachment definitions available, a pod can be created that requests a bonded interface from the Bond CNI Plugin via `bond-net`, which uses two VFs from `sriov-bond-net` that are managed by the SR-IOV CNI Plugin. The provided pod manifest [pod-bond-cni.yml](pod-bond-cni.yml) can be used. The content of the file is:
```
---
apiVersion: v1  
kind: Pod
metadata:
  name: pod-bond-cni-1
  annotations:
    k8s.v1.cni.cncf.io/networks: '[
      {"name": "sriov-bond-net",
        "interface": "net1"
      },
      {"name": "sriov-bond-net",
        "interface": "net2"
      },
      {"name": "bond-net",
        "interface": "bond0"
      }]'
spec:
  containers:
  - name: pod-bond-cni-1
    image: ubuntu:focal
    command: [ "/bin/bash", "-c" ]
    args:
      - apt update;
        apt install -y iproute2;
        sleep inf
    resources:
      requests:
        intel.com/intel_sriov_netdevice: '2'
      limits:
        intel.com/intel_sriov_netdevice: '2'
```
Deploy the pod using:
```
# kubectl apply -f pod-bond-cni.yml
```
Wait for the pod to start and install the iproute2 package, then verify the interfaces with:
```
# kubectl exec -it pod-bond-cni-1 -- ip a
```
The pod manifest sets up two named interfaces, `net1` and `net2`, which are expected by the Bond CNI Plugin as defined in the `bond-net` network attachment definition. In addition, two VF from the `intel.com/intel_sriov_netdevice` resource must be added for these interfaces to be created. The Bond CNI Plugin then takes the two interfaces and creates a third, `bond0`, which is the bonded interface.
