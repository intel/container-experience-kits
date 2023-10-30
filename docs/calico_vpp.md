# Calico VPP Dataplane Configuration Guide

The Calico VPP dataplane is in beta and should not be used in production clusters. It has had lots of testing and is pretty stable. However, chances are that some bugs are still lurking around. In addition, it still does not support all the features of Calico. More detailed information: <https://docs.tigera.io/calico/latest/getting-started/kubernetes/vpp/getting-started>

Calico VPP dataplane has only been tested on **Ubuntu 22.04 LTS**. Due to the Kubespray does not support Calico VPP dataplane yet, so we choose to install a very basic setup without any actual mesh capable CNI in kubespray stage, then install calico and calico vpp dataplane with operator based installations in `roles/calico_vpp_install`. Besides due to the Calico VPP network changes, compatilibity with other feautes in the Reference Architecture can not be fully guaranteed.

This configuration guide assumes that the **"basic"** profile is being used as a starting point. It also assumes that the deployment is on single node currently (will support 1 controller and 1 worker later).

## Prepare target servers
Calico VPP requires a dedicated interface from an Intel® Ethernet 800 Series Network Adapter.

Start by configuring the inteface on machine based on the following rules:
* The interfaces must be from an Intel® Ethernet 800 Series Network Adapter
* The interfaces must have persistent IP addresses, e.g. 12.1.152.169/8
* The servers must be reachable by the Ansible host from a separate interface and IP, e.g. 10.166.31.141/23
```
+-------------------------+           
| Master Node             |
| 10.166.31.141/23        |
|                         |
|                         |
|       +---------------------+
|       |E810                 |
|       |12.1.152.169/8       |
|       +---------------------+
|                         |
+-------------------------+
```                                                                       

## Ansible Configuration
The `inventory.ini` file must be updated with the persistent IP addresses assigned to each server. An example of this configuration can be seen below:
```
[all]
<master hostname> ansible_host=10.166.31.141 ip=12.1.152.169 ansible_user=USER ansible_password=XXXX
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
```

The following variables in `group_vars/all.yml` must be changed to support Calico VPP:
```
kube_network_plugin: cni
calico_network_backend: vxlan
kube_network_plugin_multus: false
hugepages_enabled: true
number_of_hugepages_1G: 16
calico_vpp:
  enabled: true
```

## Post Deployment
Once the deployment has completed, check the status of the Calico VPP deployment.

Check node status:
```
# kubectl get nodes -A -o wide
NAME  STATUS  ROLES  AGE  VERSION  INTERNAL-IP  EXTERNAL-IP  OS-IMAGE  KERNEL-VERSION  CONTAINER-RUNTIME
<nodename>  Ready  control-plane  12h  v1.27.1  12.1.152.169  <none>  Ubuntu 22.04.2 LTS  5.15.0-72-generic   docker://20.10.20

# kubectl describe node <nodename> | grep projectcalico
projectcalico.org/IPv4Address: 12.1.152.169/8
projectcalico.org/IPv4VXLANTunnelAddr: 10.244.66.64
```
Check pod status:
```
# kubectl get pods -n calico-vpp-dataplane
NAME                    READY   STATUS    RESTARTS   AGE
calico-vpp-node-48pnm   2/2     Running   0          12h
```
Check E810 NIC interfaces for VPP:
```
# ethtool -i xxx
driver: tun
version: 1.6
...
```
Check the configured network subnet for containers:
```
# calicoctl get ippool -o wide
NAME          CIDR   NAT   IPIPMODE   VXLANMODE   DISABLED   DISABLEBGPEXPORT   SELECTOR
default-ipv4-ippool   10.244.0.0/16   true   Never   CrossSubnet   false   false   all()
```
Check calico vpp status:
```
# calivppctl vppctl <nodename>
    _______    _        _   _____  ___
 __/ __/ _ \  (_)__    | | / / _ \/ _ \
 _/ _// // / / / _ \   | |/ / ___/ ___/
 /_/ /____(_)_/\___/   |___/_/  /_/

# show hardware-interfaces
Name                              Idx   Link  Hardware
TwentyFiveGigabitEthernet43/0/3    1     up   TwentyFiveGigabitEthernet43/0/3
...

# show int addr
TwentyFiveGigabitEthernet43/0/3 (up):
  L3 12.1.152.169/8
...
tap0 (up):
  L3 12.1.152.169/32 ip4 table-id 1013904223 fib-idx 3
```
Create 2 test pods for simple check:
```
# kubectl run test --image=busybox --command -- tail -f /dev/null
pod/test created
# kubectl exec test -- ip a show dev eth0
2: eth0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1450 qdisc mq qlen 500
    link/[65534]
    inet 10.244.66.100/32 scope global eth0
       valid_lft forever preferred_lft forever

# kubectl run test1 --image=busybox --command -- tail -f /dev/null
pod/test1 created
# kubectl exec test1 -- ip a show dev eth0
2: eth0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1450 qdisc mq qlen 500
    link/[65534]
    inet 10.244.66.101/32 scope global eth0
       valid_lft forever preferred_lft forever
# kubectl exec test1 -- ping 10.244.66.100
PING 10.244.66.100 (10.244.66.100): 56 data bytes
64 bytes from 10.244.66.100: seq=0 ttl=63 time=0.327 ms
64 bytes from 10.244.66.100: seq=1 ttl=63 time=0.823 ms
64 bytes from 10.244.66.100: seq=2 ttl=63 time=0.417 ms

# calicoctl get workloadEndpoint -o wide
NAME    WORKLOAD   NODE    NETWORKS     INTERFACE    PROFILES                   NATS
xxx-k8s-test-eth0    test   <nodename>   10.244.66.100/32   cali1037a54e65e   kns.default,ksa.default.default
xxx-k8s-test1-eth0   test1  <nodename>   10.244.66.101/32   cali99c376db89a   kns.default,ksa.default.default
```




