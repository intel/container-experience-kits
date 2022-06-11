# SR-IOV CNI Plugin
This example shows how to use the SR-IOV CNI Plugin to attach SR-IOV Virtual Functions (VFs) using using the host's kernel VF driver to pods in Kubernetes.

## Check Network Configuration
When SR-IOV CNI Plugin is enabled, an example network attachment definition is created by default. Start by checking that this definition is available:
```
# kubectl get net-attach-def -A
NAME            AGE 
sriov-net       4d3h
```

## Deploy Workload
With the network attachment definition available, a workload can be deployed that requests an interface through the SR-IOV CNI Plugin. The provided pod manifest [pod-sriov-netdevice.yml](pod-sriov-netdevice.yml) can be used. The content of the file is:
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
Note that the SR-IOV CNI Plugin functionality is requested through `k8s.v1.cni.cncf.io/networks: sriov-net`, while the actual SR-IOV VF is requested through pod resources as `intel.com/intel_sriov_netdevice: '1'`. The resources for each worker node can be seen using:
```
# kubectl get node <worker node> -o json | jq '.status.allocatable'
``` 

To deploy the pod, run:
```
# kubectl apply -f pod-sriov-netdevice.yml
```

## Verify Network
Once the pod is running and the iproute2 package has been installed, verify that the `sriov-net` interface has been added to the pod:
```
# kubectl exec pod-sriov-netdevice-1 -- ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
3: eth0@if72: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP group default
    link/ether 32:b8:e3:04:c8:93 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.244.1.29/24 brd 10.244.1.255 scope global eth0
       valid_lft forever preferred_lft forever
14: net1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether de:05:9d:bc:62:f3 brd ff:ff:ff:ff:ff:ff
    inet 10.56.217.173/24 brd 10.56.217.255 scope global net1
       valid_lft forever preferred_lft forever
```
The interface `net1` is the SR-IOV interface added via the `sriov-net` network attachment definition, which also assigns it an IP address.
