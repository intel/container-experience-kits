# Application Device Queues (ADQ) Configuration Guide

As an experimental feature, it is possible to enable ADQ with Calico using VXLAN and eBPF.

This feature utilizes [ADQ Kubernetes Plugins](https://github.com/intel/adq-k8s-plugins) to make queues available as a Kubernetes resource through an Intel® Ethernet 800 Series
Network Adapter.

ADQ has only been tested on **Ubuntu 22.04 LTS**, and due to the network changes needed to support ADQ with Calico using VXLAN and eBPF, compatilibity with other feautes in the Reference Architecture can not be guaranteed.

This configuration guide assumes that the **"build_your_own"** profile is being used as a starting point. It also assumes that the deployment consists of 1 controller and 1 worker.

## Prepare target servers
The ADQ feature requires a direct connection between servers through a dedicated interface from an Intel® Ethernet 800 Series Network Adapter.

Start by configuring the inteface on each machine based on the following rules:
* The interfaces must be from an Intel® Ethernet 800 Series Network Adapter
* The interfaces must have persistent IP addresses, e.g. 192.168.10.10/24 (controller) and 192.168.10.11/24 (worker)
* The interfaces must be in the same subnet
* The interfaces must have the same name, e.g. "adqintf"
* The servers must be reachable by the Ansible host from a separate interface and IP, e.g. 10.10.10.10/24 (controller) and 10.10.10.11/24 (worker)
```
+-------------------------+                  +-------------------------+
| Controller Node         |                  | Worker Node             |
| 10.10.10.10/24          |                  | 10.10.10.11/24          |
|                         |                  |                         |
|                         |                  |                         |
|       +---------------------+          +---------------------+       |
|       |adqintf              |          |adqintf              |       |
|       |192.168.10.10/24     |----------|192.168.10.11/24     |       |
|       +---------------------+          +---------------------+       |
|                         |                  |                         |
+-------------------------+                  +-------------------------+
```                                                                       

## Ansible Configuration
The `inventory.ini` file must be updated with the persistent IP addresses assigned to each server. An example of this configuration can be seen below:
```
[all]
<controller hostname> ansible_host=10.10.10.10 ip=192.168.10.10 ansible_user=USER ansible_password=XXXX
<worker hostname> ansible_host=10.10.10.11 ip=192.168.10.11 ansible_user=USER ansible_password=XXXX
localhost ansible_connection=local ansible_python_interpreter=/usr/bin/python3
```

The following variables in `group_vars/all.yml` must be changed to support ADQ:
```
container_runtime: containerd
cert_manager_enabled: true
calico_bpf_enabled: true
registry_enable: true
registry_local_address: "192.168.10.10:{{ registry_nodeport }}" # Use the persistent IP for ADQ from the controller
adq_dp:
  enabled: true
  interface_address: "192.168.10.10" ## IP of the persistent IP for ADQ from the controller
  interface_name: "adqintf" ## Name of the persistent interfaces for ADQ
```
In addition, if proxies are configured make sure to include the persistent IP addresses for ADQ (192.168.10.10, 192.168.10.11) in the `additional_no_proxy` list.

The following variables in `host_vars/<worker hostname>.yml` must be updated to support ADQ:
```
adq_dp:
  enabled: true
  interface_address: "192.168.10.11" ## Use the persistent IP for ADQ from the worker
```

## Post Deployment
Once the deployment has completed, check the status of the ADQ deployment.

Start by verifying that ADQ pods are running in the cluster. From the controller, check pod status:
```
$ kubectl get pods -n kube-system
NAME                                       READY   STATUS    RESTARTS   AGE
adq-cni-dp-jlzgk                           2/2     Running   0          3h30m
adq-cni-dp-lmzb9                           2/2     Running   0          3h30m
(...)
```

Then, check the ADQ resources available on each of the nodes:
```
$ kubectl get nodes -o json | jq '.items[].status.allocatable'
{
  "cpu": "143750m",
  "ephemeral-storage": "814196266480",
  "hugepages-1Gi": "0",
  "hugepages-2Mi": "0",
  "memory": "259287452Ki",
  "net.intel.com/adq": "4", # 4 ADQ resources available
  "pods": "110"
}
{
  "cpu": "142",
  "ephemeral-storage": "814196266480",
  "hugepages-1Gi": "0",
  "hugepages-2Mi": "0",
  "memory": "259024656Ki",
  "net.intel.com/adq": "4", # 4 ADQ resources available
  "pods": "110"
}
```

On both the controller and worker nodes, check that queues have been created for the persistent interface for ADQ:
```
# replace "adqintf" below with the name of the persistant interface
$ tc qdisc show dev adqintf | head -n4
qdisc mqprio 8002: root tc 6 map 0 1 2 3 4 5 0 0 0 0 0 0 0 0 0 0
             queues:(0:15) (16:19) (20:23) (24:27) (28:31) (32:32)
             mode:channel
             shaper:dcb
```
The above shows different traffic classes. `(0:15)` is the default class of 16 queues, `(16:19) (20:23) (24:27) (28:31)` are the 4 classes of 4 queues each, which are the resources that are available in Kubernetes as `net.intel.com/adq`, lastly `(32:32)` is the shared class with 1 queue, used by the ADQ Kubernetes Plugin

To test request and allocation of these resources, the following two pods kan be deployed:

Use the below to run a test pod on the controller node:
```
---
apiVersion: v1
kind: Pod
metadata:
  name: adq-test-controller
  namespace: kube-system
  annotations:
    net.v1.intel.com/adq-config: '[ { "name": "adq-test-controller", "ports": { "local": ["6379/  TCP"] } } ]'
spec:
  nodeSelector:
    kubernetes.io/hostname: "<controller hostname>" # Update this line with the hostname of the controller
  tolerations:
    - key: "node-role.kubernetes.io/control-plane"
      effect: "NoSchedule"
      operator: "Exists"
  containers:
    - name: adq-test-controller
      image: ubuntu:focal
      command: [ "/bin/bash", "-c" ]
      args: [ "sleep inf" ]
      ports:
        - containerPort: 6379
      resources:
        limits:
          net.intel.com/adq: 1
```

Use the below to run a test pod on the worker node:
```
---
apiVersion: v1
kind: Pod
metadata:
  name: adq-test-worker
  namespace: kube-system
  annotations:
    net.v1.intel.com/adq-config: '[ { "name": "adq-test-worker", "ports": { "local": ["6379/  TCP"] } } ]'
spec:
  containers:
    - name: adq-test-worker
      image: ubuntu:focal
      command: [ "/bin/bash", "-c" ]
      args: [ "sleep inf" ]
      ports:
        - containerPort: 6379
      resources:
        limits:
          net.intel.com/adq: 1
```

Verify that the two pods are running from the controller:
```
$ kubectl get pods -n kube-system
NAME                                       READY   STATUS    RESTARTS   AGE
adq-cni-dp-jlzgk                           2/2     Running   0          4h18m
adq-cni-dp-lmzb9                           2/2     Running   0          4h18m
adq-test-controller                        1/1     Running   0          9m46s # pod running on controller node
adq-test-worker                            1/1     Running   0          9m38s # pod running on worker node
```

Check that ADQ resources have been allocated by Kubernetes.:
```
$ kubectl describe node <controller or worker node>
(...)
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests        Limits
  --------           --------        ------
  cpu                295m (0%)       300m (0%)
  memory             179886080 (0%)  814572800 (0%)
  ephemeral-storage  0 (0%)          0 (0%)
  hugepages-1Gi      0 (0%)          0 (0%)
  hugepages-2Mi      0 (0%)          0 (0%)
  net.intel.com/adq  1               1
(...)
```
The `net.intel.com/adq` line above shows that one of the resources has been requested and allocated. This should be the case on both the controller and worker nodes.

Lastly, check on both the controller and worker nodes that the filter for port 6379 (defined for each of the above pods) has been set correctly:
```
$ tc filter show dev vxlan.calico ingress
filter protocol ip pref 1 flower chain 0
filter protocol ip pref 1 flower chain 0 handle 0x2 hw_tc 1
  eth_type ipv4
  ip_proto tcp
  dst_ip 10.244.88.138
  dst_port 6379
  in_hw in_hw_count 1
filter protocol all pref 49152 bpf chain 0
filter protocol all pref 49152 bpf chain 0 handle 0x1 calico_from_hos:[417] direct-action not_in_hw id 417 tag c53675a0f3db3f12 jited
```

```
$ tc filter show dev vxlan.calico egress
filter protocol ip pref 1 flower chain 0
filter protocol ip pref 1 flower chain 0 handle 0x2
  eth_type ipv4
  ip_proto tcp
  src_ip 10.244.88.138
  src_port 6379
  not_in_hw
        action order 1: skbedit  priority :1 pipe
         index 2 ref 1 bind 1

filter protocol all pref 49152 bpf chain 0
filter protocol all pref 49152 bpf chain 0 handle 0x1 calico_to_host_:[416] direct-action not_in_hw id 416 tag cba74d32c9f1088b jited
```

At this point the two pods, 'adq-test-controller' and 'adq-test-worker', can be deleted again. Once the pods are deleted, the above checks can be done again to see that the ADQ resources have been freed in Kubernetes, and that the filters have been removed:
```
$ kubectl describe node <controller or worker node>
(...)
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests        Limits
  --------           --------        ------
  cpu                830m (0%)       1300m (0%)
  memory             201400320 (0%)  1070572800 (0%)
  ephemeral-storage  0 (0%)          0 (0%)
  hugepages-1Gi      0 (0%)          0 (0%)
  hugepages-2Mi      0 (0%)          0 (0%)
  net.intel.com/adq  0               0
(...)
```

```
$ tc filter show dev vxlan.calico ingress
filter protocol all pref 49152 bpf chain 0
filter protocol all pref 49152 bpf chain 0 handle 0x1 calico_from_hos:[417] direct-action not_in_hw id 417 tag c53675a0f3db3f12 jited
```

```
$ tc filter show dev vxlan.calico egress
filter protocol all pref 49152 bpf chain 0
filter protocol all pref 49152 bpf chain 0 handle 0x1 calico_to_host_:[416] direct-action not_in_hw id 416 tag cba74d32c9f1088b jited
```
