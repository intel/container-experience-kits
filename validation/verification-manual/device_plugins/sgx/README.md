# SGX Device Plugin
This example shows how to check resources available through the SGX Device Plugin.

## Verify Node Resources
List the allocatable node resources for the target worker node:
```
# kubectl get node <worker node> -o json | jq '.status.allocatable'
{
  "cpu": "95550m",
  "ephemeral-storage": "353450007582",
  "hugepages-1Gi": "4Gi",
  "hugepages-2Mi": "256Mi",
  "intel.com/node1_ens801f0_intelnics_1": "1",
  "intel.com/node1_ens801f0_intelnics_2": "4",
  "intel.com/node1_ens801f0_intelnics_3": "1",
  "intel.com/node1_ens801f1_intelnics_1": "4",
  "memory": "518294736Ki",
  "pods": "110",
  "power.intel.com/balance-performance": "76",
  "power.intel.com/balance-performance-node1": "76",
  "power.intel.com/balance-power": "102",
  "power.intel.com/balance-power-node1": "102",
  "power.intel.com/performance": "51",
  "power.intel.com/performance-node1": "51",
  "qat.intel.com/generic": "32",
  "sgx.intel.com/enclave": "20",
  "sgx.intel.com/epc": "4261412864",
  "sgx.intel.com/provision": "20"
}
```
The relevant resources are `sgx.intel.com/*`
