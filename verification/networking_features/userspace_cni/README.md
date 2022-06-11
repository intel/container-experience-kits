# Userspace CNI Plugin
This example shows how to use the Userspace CNI Plugin with DPDK enchanced Open vSwitch (OVS-DPDK) to attach vhostuser interfaces to pods in Kubernetes.

## Check Network Configuration
When Userspace CNI is enabled, an example network attachment definintion is created by default. Start by checking that this definition is available:
```
# kubectl get net-attach-def
NAME            AGE
userspace-ovs   7d
```

## Deploy Workload
With the network attachment definition available, a workload can be deployed that requests an interface through the Userspace CNI Plugin. The provided pod manifest [pod-userspace.yml](pod-userspace.yml) can be used. The content of the file is:
```
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-userspace-1
  annotations:
    k8s.v1.cni.cncf.io/networks: userspace-ovs
spec:
  containers:
  - name: pod-userspace-1
    image: ubuntu:focal
    command: [ "/bin/bash", "-c" ]
    args: [ "sleep inf" ]
    volumeMounts:
    - mountPath: /vhu/
      name: shared-dir
  volumes:
  - name: shared-dir
    hostPath:
      path: /var/lib/cni/vhostuser/
```
In addition to requesting the network interface through `k8s.v1.cni.cncf.io/networks: userspace-ovs`, a volume mount is added that is used for the vhostuser socket created by the Userspace CNI.

Deploy the pod:
```
# kubectl apply -f pod-userspace.yml
```

## Verify Network
Start by verifying that a vhostuser socket has been added to the pod:
```
# kubectl exec pod-userspace-1 -- ls /vhu/
35998a9a2ce2-net1
```
If there are multiple worker nodes in the cluster, check which one the pod has been deployed on:
```
# kubectl describe pod pod-userspace-1 | grep Node: 
Node:         node1/<node IP>
```
Connect to that node using the IP found above, and verify that the vhostuser socket and interface has been added to OVS-DPDK:
```
# ovs-vsctl show
b11c98d8-080f-4cad-adaa-467256809265
    Bridge br0
        datapath_type: netdev
        Port br0
            Interface br0
                type: internal
        Port "35998a9a2ce2-net1"
            Interface "35998a9a2ce2-net1"
                type: dpdkvhostuser
    ovs_version: "2.17.1"
```
At this point, the vhostuser socket is ready to use in the pod. The steps for using VPP as the vSwitch are similar, but instead of the Userspace CNI resource name userspace-ovs, use userspace-vpp.
