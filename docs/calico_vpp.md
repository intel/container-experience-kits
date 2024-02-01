# Calico VPP Dataplane Configuration Guide

The Calico VPP dataplane is in beta and should not be used in production clusters. It has had lots of testing and is pretty stable. However, chances are that some bugs are still lurking around. In addition, it still does not support all the features of Calico. More detailed information: <https://docs.tigera.io/calico/latest/getting-started/kubernetes/vpp/getting-started>

Calico VPP dataplane has only been tested on **Ubuntu 22.04 LTS**. Due to the Kubespray does not support Calico VPP dataplane yet, so we choose to install a very basic setup without any actual mesh capable CNI in kubespray stage, then install calico and calico vpp dataplane with operator based installations in `roles/calico_vpp_install`. Besides due to the Calico VPP network changes, compatilibity with other feautes in the Reference Architecture can not be fully guaranteed.

This configuration guide assumes that the **"basic"** profile is being used as a starting point. It now can deploy among nodes(here, we take 1C+2W=2H as example).

## Prepare target servers
Calico VPP requires a dedicated interface from an Intel® Ethernet 800 Series Network Adapter.

Start by configuring the inteface on machine based on the following rules:
* The interfaces must be from an Intel® Ethernet 800 Series Network Adapter
* The interfaces must have persistent IP addresses, e.g. 10.10.10.10, 10.10.10.11
* The servers must be reachable by the Ansible host from a separate interface and IP, e.g. 192.168.100.100, 192.168.100.101
```
+-------------------------+                  +-------------------------+
| Master Node             |                  | Worker Node             |
| 192.168.100.100         |                  | 192.168.100.101         |
|                         |                  |                         |
|                         |                  |                         |
|       +---------------------+          +---------------------+       |
|       |ens108              |          |ens108               |       |
|       |10.10.10.10         |----------|10.10.10.11          |       |
|       +---------------------+          +---------------------+       |
|                         |                  |                         |
+-------------------------+                  +-------------------------+
```                                                                       

## Ansible Configuration
The `inventory.ini` file must be updated with the persistent IP addresses assigned to each server. An example of this configuration can be seen below:
```
[all]
<master hostname> ansible_host=192.168.100.100 ip=10.10.10.10 ansible_user=USER ansible_password=XXXX
<worker hostname> ansible_host=192.168.100.101 ip=10.10.10.11 ansible_user=USER ansible_password=XXXX
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
```

The following variables in `group_vars/all.yml` must be changed to support Calico VPP:
```
kube_network_plugin: cni
calico_network_backend: vxlan
kube_network_plugin_multus: false
calico_vpp:
  enabled: true

```

The following variables in `host_vars/<xxx>.yml` must be changed to support Calico VPP:
```
hugepages_enabled: true
number_of_hugepages_1G: 16
install_dpdk: true
```

## Post Deployment
Once the deployment has completed, check the status of the Calico VPP deployment.

Check node status:
```
# kubectl get nodes -A -o wide
NAME                STATUS  ROLES         AGE  VERSION    INTERNAL-IP  EXTERNAL-IP  OS-IMAGE        KERNEL-VERSION  CONTAINER-RUNTIME
<master nodename>   Ready  control-plane  15h   v1.28.3   10.10.10.10  <none>  Ubuntu 22.04.2 LTS   5.15.0-72-generic   containerd://1.7.8
<worker nodename>   Ready  <none>         15h   v1.28.3   10.10.10.11 <none>  Ubuntu 22.04.2 LTS   5.15.0-72-generic   containerd://1.7.8

# kubectl describe node <master nodename> | grep projectcalico
projectcalico.org/IPv4Address: 10.10.10.10
projectcalico.org/IPv4VXLANTunnelAddr: 10.244.143.64

# kubectl describe node <worker nodename> | grep projectcalico
projectcalico.org/IPv4Address: 10.10.10.11
projectcalico.org/IPv4VXLANTunnelAddr: 10.244.200.193
```
Check pod status:
```
# kubectl get pods -n calico-vpp-dataplane
NAME                    READY   STATUS    RESTARTS      AGE
calico-vpp-node-9swvq   2/2     Running   1 (15h ago)   15h
calico-vpp-node-m42k9   2/2     Running   2 (15h ago)   15h
```
Check E810 NIC interfaces for VPP:
```
# ethtool -i ens108
driver: tun
version: 1.6
firmware-version:
expansion-rom-version:
bus-info: tap
...
```
Check the configured network subnet for containers:
```
# calicoctl get ippool -o wide
NAME          CIDR   NAT   IPIPMODE   VXLANMODE   DISABLED   DISABLEBGPEXPORT   SELECTOR
default-ipv4-ippool   10.244.0.0/16   true   Never   CrossSubnet   false   false   all()
```
Check calico vpp status(take master node as example):
```
# calivppctl vppctl <master nodename>
    _______    _        _   _____  ___
 __/ __/ _ \  (_)__    | | / / _ \/ _ \
 _/ _// // / / / _ \   | |/ / ___/ ___/
 /_/ /____(_)_/\___/   |___/_/  /_/

vpp# show hardware-interfaces
Name                Idx   Link  Hardware
HundredGigabitEthernet98/0/0       1     up   HundredGigabitEthernet98/0/0
  Link speed: 100 Gbps
...
vpp# show int addr
HundredGigabitEthernet98/0/0 (up):
  L3 10.10.10.10/8
...
tap0 (up):
  L3 10.10.10.10/32 ip4 table-id 1013904223 fib-idx 3
```
Create 2 test pods for simple check:
```
# kubectl run test --image=busybox --overrides='{"spec": { "nodeSelector": {"kubernetes.io/hostname": "<master nodename>"}}}' --command -- tail -f /dev/null
pod/test created
# kubectl exec test -- ip a show dev eth0
2: eth0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1450 qdisc mq qlen 500
    link/[65534]
    inet 10.244.143.87/32 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::3e9d:58cb:257b:93ee/64 scope link flags 800
       valid_lft forever preferred_lft forever

# kubectl run test1 --image=busybox --overrides='{"spec": { "nodeSelector": {"kubernetes.io/hostname": "<worker nodename>"}}}' --command -- tail -f /dev/null
pod/test1 created
# kubectl exec test1 -- ip a show dev eth0
2: eth0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1450 qdisc mq qlen 500
    link/[65534]
    inet 10.244.200.215/32 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::d8cc:3cd5:45a4:4310/64 scope link flags 800
       valid_lft forever preferred_lft forever
# kubectl exec test1 -- ping 10.244.143.87
PING 10.244.143.87 (10.244.143.87): 56 data bytes
64 bytes from 10.244.143.87: seq=0 ttl=62 time=0.665 ms
64 bytes from 10.244.143.87: seq=1 ttl=62 time=1.525 ms
64 bytes from 10.244.143.87: seq=2 ttl=62 time=0.741 ms

# calicoctl get workloadEndpoint -o wide
NAME                WORKLOAD      NODE    NETWORKS     INTERFACE    PROFILES                   NATS
xxx-k8s-test-eth0   test    <master nodename>   10.244.143.87/32    cali1037a54e65e   kns.default,ksa.default.default
xxx-k8s-test1-eth0  test1   <worker nodename>   10.244.200.215/32   cali99c376db89a   kns.default,ksa.default.default
```




