# What is VM + BM Mixed configuration


There is a requirement that a cluster is to be composited of VMs and Baremetal hosts. The role of VMs and BM hosts are flexible.

In VMRA, we create VXLAN bridges on VM hosts. The one on first VM host is special -- it is a DHCP VXLAN bridge. Other VMs (even for those on other VM hosts) will get their VXLAN ip from this bridge through DHCP.

In order to composite the mixed cluster, we reused the same VXLAN way on BM host. it is a simple VXLAN bridge interface.Instead of requesting DHCP from first VM host, we choose to assign fixed VXLAN IP for BM host. The default DHCP pool range is from 172.31.0.3 ~ 172.31.0.100 and thus leaves the IP above 172.31.0.100 to be assigned to BM hosts.

## group_vars/all.yml specific options

There is one special requirement for CNI selection: calico with VXLAN backend must be selected for the mixed cluster. Other CNI may work too, but not verified.

```
kube_network_plugin: calico
```
```
calico_network_backend: vxlan
```
```
calico_mtu: 1390
```

## Mixed BM host specific options

The Mixed BM host need define two new parameters in host_vars compared with normal BMRA host.
examples:

```
vxlan_gw_ip: "172.31.0.101/24"
```
```
vxlan_physical_network: "11.0.0.0/8"
```
Note: please select the proper subnet of vxlan physical network according to your real situation. Subnet must be the same as it is used for vm_hosts.
Note: vxlan_gw_ip must belong to the same subnet as for vm_host.


The vxlan_gw_ip variable defines the VXLAN bridge IP on Mixed BM host. This is also the IP that the cluster will "see" the node.

The vxlan_physical_network is used to auto select the physical NIC that will carry on the VXLAN transport.

This two parameters are very similar with the ones on VM host host_vars unless only the first VM host requires vxlan_gw_ip.

# Example inventory.ini for Mixed case
In this example, we have vm-ctrl-1 and vm-work-1 as they are from traditional VMRA configuration. The difference is we also defined a "bm-1" host which will be a kube_node in the coming cluster.
```
[all]
host-for-vms-1 ansible_host=10.67.116.xxx ip=10.67.116.xxx ansible_user=root
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
bm-1 ansible_host=10.67.117.xxx ip=10.67.117.xxx ansible_user=root

[vm_host]
host-for-vms-1

[kube_control_plane]
#vm-ctrl-1

[etcd]
#vm-ctrl-1

[kube_node]
bm-1

[k8s_cluster:children]
kube_control_plane
kube_node

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```

During the ansible execution, the new created inventory_vm.ini will look like this:
```
[all]
host-for-vms-1 ansible_host=10.67.116.xxx ip=10.67.116.xxx ansible_user=root
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
bm-1 ansible_host=172.31.0.101 ip=172.31.0.101 ansible_user=root
vm-ctrl-1 ansible_host=172.31.0.60 ip=172.31.0.60 ansible_user=root
vm-work-1 ansible_host=172.31.0.47 ip=172.31.0.47 ansible_user=root

[vm_host]
host-for-vms-1

[kube_control_plane]
vm-ctrl-1

[etcd]
vm-ctrl-1

[kube_node]
bm-1
vm-work-1

[k8s_cluster:children]
kube_control_plane
kube_node

[all:vars]
ansible_python_interpreter=/usr/bin/python3
```
