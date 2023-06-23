# Multus CNI Plugin
This example shows how to use the Multus CNI Plugin to add additional interfaces to a pod in Kubernetes. In this example we use the `macvlan` CNI Plugin to configure the interface through a network attachment definition, which Multus CNI Plugin then adds to the pod.

## Create Network Configuration
To create the `macvlan` network attachment definition, the provided manifest [macvlan-multus.yml](macvlan-multus.yml) can be used. The content of the file is:
```
---
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: macvlan-multus-1
spec:
  config: '{
    "cniVersion": "0.3.0",
    "type": "macvlan",
    "master": "{{ interface }}",
    "mode": "bridge",
    "ipam": {
      "type": "host-local",
      "ranges": [
        [ {
          "subnet": "10.10.0.0/16",
          "rangeStart": "10.10.1.20",
          "rangeEnd": "10.10.3.50",
          "gateway": "10.10.0.254"
        } ]
      ]
    }
  }'
```
Note that the `"{{ interface }}"` value must be updated to match an interface on a worker node, e.g. `"ens786f1"`.

Once the manifest has been updated, apply it to the Kubernetes cluster:
```
# kubectl apply -f macvlan-multus.yml
```
Check that the network attachment definition has been created:
```
# kubectl get net-attach-def
NAME               AGE 
macvlan-multus-1   4d1h
```

## Deploy Workload
Once the network is available in the cluster, we can deploy a workload requests an interface through the Multus CNI Plugin. The provided pod manifest [pod-multus.yml](pod-multus.yml) can be used. The content of the file is:
```
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-multus-1
  annotations:
    k8s.v1.cni.cncf.io/networks: macvlan-multus-1
spec:
  containers:
  - name: pod-multus-1
    image: ubuntu:focal
    command: [ "/bin/bash", "-c" ]
    args:
      - apt update;
        apt install -y iproute2;
        sleep inf
```
Deploy the pod:
```
# kubectl apply -f pod-multus.yml
```

## Verify Network
Once the pod is running, verify that the `macvlan` interface has been added to the pod and assigned an IP address:
```
# kubectl exec pod-multus-1 -- ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000 
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
3: eth0@if71: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP group default
    link/ether 7e:33:5e:5b:1b:4f brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.244.1.28/24 brd 10.244.1.255 scope global eth0
       valid_lft forever preferred_lft forever
4: net1@if11: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 8e:c0:49:08:8a:ab brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.10.1.21/16 brd 10.10.255.255 scope global net1
       valid_lft forever preferred_lft forever
```
The interface `net1@if11` is the interface added by Multus CNI Plugin using the `macvlan` CNI. As it is seen above, the interface has been assigned an IP address from the range defined in the network attachment definition `macvlan-multus-1` that was requested in the pod manifest.
