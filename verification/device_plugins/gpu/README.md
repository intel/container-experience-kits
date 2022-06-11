# GPU Device Plugin
This example shows how to check resources available through the GPU Device Plugin

## Verify Node Resources
List the allocatable metadata lables for the target worker node:
```
kubectl get node <work node name> -o json |jq .metadata.labels
{
  "beta.kubernetes.io/arch": "amd64",
  "beta.kubernetes.io/os": "linux",
  "feature.node.kubernetes.io/cpu-cpuid.ADX": "true",
  ……
  "feature.node.kubernetes.io/intel.qat": "true",
  "feature.node.kubernetes.io/kernel-version.full": "5.4.48",
  "feature.node.kubernetes.io/kernel-version.major": "5",
  "feature.node.kubernetes.io/kernel-version.minor": "4",
  "feature.node.kubernetes.io/kernel-version.revision": "48",
  ……
  "gpu.intel.com/cards": "card0.card1.card2.card3",
  "kubernetes.io/arch": "amd64",
  "kubernetes.io/hostname": "as09-16-wpr",
  "kubernetes.io/os": "linux",
  "node-role.kubernetes.io/worker": ""
}
```
The relevant label is `gpu.intel.com/cards`
