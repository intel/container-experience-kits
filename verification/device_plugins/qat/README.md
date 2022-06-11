# QAT Device Plugin
This example show how to use the QAT Device Plugin for assigning Virtual Functions (VFs) to workloads in Kubernetes. The QAT deivces provide access to accelerated cryptographic and compression features.

## Verify Node Resources
Start by listing allocatable node resources for the target worker node:
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
In the above, the QAT device plugin resources are `qat.intel.com/generic`.

## Verifying QAT Devices
For this test we will create a workload and assign a QAT device to the pod.

### Deploy Workload
To the test QAT Device Plugin, the provided pod manifest [pod-qat.yml](pod-qat.yml) can be used. The content of the file is:
```
---
apiVersion: v1  
kind: Pod
metadata:
  name: pod-qat-1
spec:
  containers:
  - name: pod-qat-1
    image: ubuntu:focal
    command: [ "/bin/bash", "-c" ]
    args: [ "sleep inf" ]
    resources:
      requests:
        qat.intel.com/generic: '1'
      limits:
        qat.intel.com/generic: '1'
```
Now deploy the pod:
```
# kubectl apply -f pod-qat.yml
```

### Verify Pod Resources
Once running, verify that the QAT device is avaialble in the pod:
```
# kubectl exec pod-qat-1 -- env | grep QAT
QAT0=0000:3e:02.1
```
