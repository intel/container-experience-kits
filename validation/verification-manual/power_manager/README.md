# Check Intel Power Manager (Balance Performance Power-Profile & Sample Power-Pods)
Sample pods can be deployed by setting `deploy_example_pods: true` in group vars. Following are the results that can be obtained from Power Manager work
```
# kubectl get pods -n intel-power
NAME                                 READY   STATUS    RESTARTS   AGE
balance-performance-power-pod        1/1     Running   0          33m
balance-power-power-pod              1/1     Running   0          33m
controller-manager-f584c9458-p5llp   1/1     Running   0          34m
performance-power-pod                1/1     Running   0          33m
power-node-agent-9dkch               2/2     Running   0          34m
```
**Note:** each profile was deployed in a separate pod

Check the power profiles:
```
# kubectl get powerprofiles -n intel-power
NAME                              AGE
balance-performance               30m
balance-performance-node1         30m
balance-power                     30m
balance-power-node1               30m
performance                       30m
performance-node1                 30m
```

You can check the frequencies that will be set by balance-performance Power Profile
```
# kubectl get PowerProfiles -n intel-power balance-performance-node1 -o yaml
apiVersion: power.intel.com/v1alpha1
kind: PowerProfile
metadata:
  creationTimestamp: "2022-02-07T20:50:44Z"
  generation: 1
  name: balance-performance-node1
  namespace: intel-power
  resourceVersion: "4790"
  uid: 3bc5d223-f31e-4fdc-8c49-8a87148a014d
spec:
  epp: balance_performance
  max: 2700
  min: 2500
  name: balance-performance-node1
```

To obtain balance-performance cores, apply the Power Profile
```
# kubectl get PowerWorkloads -n intel-power balance-performance-node1-workload -o yaml
apiVersion: power.intel.com/v1alpha1
kind: PowerWorkload
metadata:
  creationTimestamp: "2022-02-07T20:51:43Z"
  generation: 1
  name: balance-performance-node1-workload
  namespace: intel-power
  resourceVersion: "5090"
  uid: 19de2932-6ab6-4863-b664-764cc555e23d
spec:
  name: balance-performance-node1-workload
  nodeInfo:
    containers:
    - exclusiveCpus:
      - 4
      - 68
      id: 870e1d2eb4f971328d5030f97a647b8ee5fb7dae52daebec4714588e9a563667
      name: balance-performance-container
      pod: balance-performance-power-pod
      powerProfile: balance-performance-node1
    cpuIds:
    - 4
    - 68
    name: node1
  powerProfile: balance-performance-node1
```

If you want to check all the cores in your Power Nodes, you can use the following command
```
# kubectl get PowerNodes -A -o yaml
apiVersion: v1
items:
- apiVersion: power.intel.com/v1alpha1
  kind: PowerNode
  metadata:
    creationTimestamp: "2022-02-07T20:50:40Z"
    generation: 1018
    name: node1
    namespace: intel-power
    resourceVersion: "44835"
    uid: 2aa0f908-2f18-473f-989e-12c46ad2811a
  spec:
    activeProfiles:
      balance-performance-node1: true
      balance-power-node1: true
      performance-node1: true
    activeWorkloads:
    - cores:
      - 2
      - 66
      name: performance-node1-workload
    - cores:
      - 4
      - 68
      name: balance-performance-node1-workload
    - cores:
      - 3
      - 67
      name: balance-power-node1-workload
    nodeName: node1
    powerContainers:
    - exclusiveCpus:
      - 2
      - 66
      id: c152e29f49db457417beca958133e7d8d995ea7302f76073b96c5797fd20d770
      name: performance-container
      pod: performance-power-pod
      powerProfile: performance-node1
      workload: performance-node1-workload
    - exclusiveCpus:
      - 4
      - 68
      id: 870e1d2eb4f971328d5030f97a647b8ee5fb7dae52daebec4714588e9a563667
      name: balance-performance-container
      pod: balance-performance-power-pod
      powerProfile: balance-performance-node1
      workload: balance-performance-node1-workload
    - exclusiveCpus:
      - 3
      - 67
      id: 3ea83bf1369946fbe625e7fec4355de4760a1b8a1528959cd7eacb87c3e046a9
      name: balance-power-container
      pod: balance-power-power-pod
      powerProfile: balance-power-node1
      workload: balance-power-node1-workload
    sharedPools:
    - name: Default
      sharedPoolCpuIds:
      - 0
      - 1
      - 2
      - 3
      - 4
      - 5
...
```
