# DSA Device Plugin
This example shows how to check resources available through the DSA Device Plugin, on both the host and in Kubernetes.

## Verify Node Resources
Check that the DSA work queues are visible on the node:
```
# ls /sys/bus/devices/ | grep "dsa\!wq"
dsa!wq0.0  dsa!wq0.1  dsa!wq0.2  dsa!wq0.3  dsa!wq0.4  dsa!wq0.5  dsa!wq0.6  dsa!wq0.7
dsa!wq1.0  dsa!wq1.1  dsa!wq1.2  dsa!wq1.3  dsa!wq1.4  dsa!wq1.5  dsa!wq1.6  dsa!wq1.7
dsa!wq2.0  dsa!wq2.1  dsa!wq2.2  dsa!wq2.3  dsa!wq2.4  dsa!wq2.5  dsa!wq2.6  dsa!wq2.7
dsa!wq3.0  dsa!wq3.1  dsa!wq3.2  dsa!wq3.3  dsa!wq3.4  dsa!wq3.5  dsa!wq3.6  dsa!wq3.7
```

List the allocatable node resources for the target worker node:
```
# kubectl get node <worker node> -o json | jq '.status.allocatable'
{
  "cpu": "95550m",
  "dsa.intel.com/wq-user-dedicated": "16",
  "dsa.intel.com/wq-user-shared": "160",
  "ephemeral-storage": "282566437625",
  "hugepages-1Gi": "4Gi",
  "hugepages-2Mi": "0",
  "memory": "125570920Ki",
  "pods": "110"
}
```
The relevant resources are `dsa.intel.com/*`

