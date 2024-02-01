# Userspace CNI Plugin

This example shows how to use the Userspace CNI Plugin with DPDK enchanced Open vSwitch (OVS-DPDK) or VPP vSwitch to attach vhostuser interfaces to pods in Kubernetes.

## Check Network Configuration

When Userspace CNI is enabled, an example network attachment definintion is created by default. Start by checking that this definition is available:

```bash
# kubectl get net-attach-def
NAME            AGE
userspace-ovs   14h
```

## Deploy Workload

With the network attachment definition available, a workload can be deployed that requests an interface through the Userspace CNI Plugin. The provided pod manifest [pod-userspace-ovs.yml](pod-userspace-ovs.yml) can be used.
In addition to requesting the network interface through `k8s.v1.cni.cncf.io/networks: userspace-ovs`, a volume mount is added that is used for the vhostuser socket created by the Userspace CNI.

Deploy the pod:

```bash
# kubectl apply -f pod-userspace.yml
```

## Verify Network

Start by verifying that a vhostuser socket has been added to the pod:

```bash
kubectl exec pod-userspace-1 -- ls /vhu/

5dee26822a53-net1
```

If there are multiple worker nodes in the cluster, check which one the pod has been deployed on:

```bash
kubectl describe pod pod-userspace-1 | grep Node: 

Node:         node1/<node IP>
```
Connect to that node using the IP found above, and verify that the vhostuser socket and interface has been added to OVS-DPDK:

```bash
ovs-vsctl show

6836950b-fe14-42f7-823b-06ae680b88f4
    Bridge br0
        datapath_type: netdev
        Port br0
            Interface br0
                type: internal
        Port "5dee26822a53-net1"
            Interface "5dee26822a53-net1"
                type: dpdkvhostuser
    ovs_version: "2.17.2"
```

At this point, the vhostuser socket is ready to use in the pod. The steps for using VPP as the vSwitch are similar, but instead of the Userspace CNI resource name userspace-ovs, use userspace-vpp. The provided pod manifest [pod-userspace-vpp.yml](pod-userspace-vpp.yml) can be used.
