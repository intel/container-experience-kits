# This Power Manager guide should describe what exactly can be configured in group vars and host vars

# group vars
In group vars, you can enable/disable the whole power manager feature. If the feature is enabled, you need to fill power_nodes list. You can also choose to build power manager locally, to deploy sample pods, or to turn on the cluster-wide shared profile.

# host vars
In host vars, there are more options for power manager. You can configure your desired power profiles here, which are needed for power-config or sample pods. There is also configuration for node-specific shared profile and shared workload uncore frequency and c-states configuration.

# sample pods deployment
Sample pods are requesting cpu cores, which will be part of exclusive pool. To function properly, you will also need to have shared pool configured in your cluster (read more below). For this example, we are using balance-performance profile:
```
# kubectl get pods -n intel-power
NAME                                        READY   STATUS    RESTARTS   AGE
balance-performance-power-pod-node1         1/1     Running   0          71s
balance-performance-power-pod-node2         1/1     Running   0          97s
controller-manager-6f95578567-g74lw         1/1     Running   0          114s
power-node-agent-2xnd5                      1/1     Running   0          106s
power-node-agent-cptbd                      1/1     Running   0          106s
```
**Note:** You can also request different profile for each node

You need to enable global/local shared profile and shared workload to enable the Shared Pool, 
```
# default in group_vars
global_shared_profile_enabled: true # default in group_vars

# default in host_vars
local_shared_profile:
  enabled: true
shared_workload:
  enabled: true

```

If you want to check all the cores in your Power Nodes, or frequencies, which will be set by your desired profile, you can use the following command
```
# kubectl get PowerNodes -A -o yaml
apiVersion: v1
items:
- apiVersion: power.intel.com/v1
  kind: PowerNode
  metadata:
    creationTimestamp: "2023-07-12T12:06:46Z"
    generation: 4
    name: node1
    namespace: intel-power
    resourceVersion: "3514623"
    uid: 6990a520-4ea6-4cde-91e0-eef6ac058fda
  spec:
    nodeName: node1
    powerProfiles:
    - 'balance-performance: 2825000 || 2625000 || '
    sharedPool: shared-global || 1500000 || 1000000 || 0,2-72,74-143
    unaffectedCores: 0-143
- apiVersion: power.intel.com/v1
  kind: PowerNode
  metadata:
    creationTimestamp: "2023-07-12T12:06:46Z"
    generation: 1
    name: ar09-28-cyp
    namespace: intel-power
    resourceVersion: "3514271"
    uid: e76eb4ae-be6a-4dea-b6d1-5c1ae2a12ad0
  spec:
    nodeName: ar09-28-cyp
- apiVersion: power.intel.com/v1
  kind: PowerNode
  metadata:
    creationTimestamp: "2023-07-12T12:06:46Z"
    generation: 4
    name: node2
    namespace: intel-power
    resourceVersion: "3514603"
    uid: a70c4b99-e27e-4811-b85e-7aad6ad8dab6
  spec:
    nodeName: node2
    powerProfiles:
    - 'balance-performance: 2825000 || 2625000 || '
    sharedPool: shared-global || 1500000 || 1000000 || 0,2-64,66-127
    unaffectedCores: 0-127
kind: List
metadata:
  resourceVersion: ""
```
**Note:** As there is only one power config in whole cluster, all PowerProfiles from each node are applied cluster-wide
**Note:** Exclusive pool cores aren't displayed by power manager in time of making this guide, but you can see them absent in shared pool. In this case cores 1,73 for node1 and cores 1,65 for node2.

To setup Uncore Frequency, you can choose from two options:
```
# You can set up system-wide uncore frequency with:
  system_max_frequency: 2300000
  system_min_frequency: 1300000

# Or you can use die/package specific settings:
  die_selector:
    - package: 0
      die: 0
      min: 1500000
      max: 2400000
```
To check Uncore Frequency, you can use following path:
```
/sys/devices/system/cpu/intel_uncore_frequency/package_XY_die_XY
```
You can then check files 'max_freq_khz' or 'min_freq_khz' which should store your desired Uncore Frequency values.
**Note:** Valid min and max values are determined by hardware. Die config will precede Package config, which will precede system-wide config.
**Note:** To prevent both min and max frequency values of being the same value, please set "System BIOS > System Profile Settings > Uncore Frequency" from "Maximum" to "Dynamic" in machine's BIOS.

To set up C-States, you can choose from three different options:
```
# First option will enable/disable desired_state for all cores in shared pool
  shared:
    desired_state: true

# Second option will enable/disable desired_state for balance-performance exclusive pool
  profile_exclusive:
    balance-performance:
      desired_state: false
  
# Third option will enable/disable desired_state for specific_core
  core:
    "specific_core":
      desired_state: true
```

To check C-States, you can use following path:
```
# /sys/devices/system/cpu/cpuX/cpuidle/stateY
```
You can check all C-State information there. For example:
```
# cat /sys/devices/system/cpu/cpu3/cpuidle/state3/name
C6

# cat /sys/devices/system/cpu/cpu3/cpuidle/state3/disable
1
```
To check your desired scaling driver, you can do following:
```
# cat /sys/devices/system/cpu/cpuX/cpufreq/scaling_driver
```
**Note:** Scaling driver's available are: intel_pstate, intel_cpufreq

To check your desired scaling governor:
```
# cat /sys/devices/system/cpu/cpuX/cpufreq/scaling_governor
```
You can also check all available scaling governors:
```
# cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors
```
Time of Day can be used to schedule change of powerProfile or C-State for sharedPool, or powerProfile for sample pod. Schedule examples:
```
schedule:
  - time: "14:24"
    # powerProfile sets the profile for the shared pool
    powerProfile: balance-performance

    # this transitions exclusive pods matching a given label from one profile to another
    # please ensure that only pods to be used by power manager have this label
    pods:
      - labels:
          matchLabels:
            power: "true"
        target: balance-performance
      - labels:
          matchLabels:
            special: "false"
        target: balance-performance

    # cState field simply takes a cstate spec
    cState:
      sharedPoolCStates:
        C1: false
        C6: true

  - time: "14:26"
    powerProfile: performance
    cState:
      sharedPoolCStates:
        C1: true
        C6: false

  - time: "14:28"
    powerProfile: balance-power
    pods:
      - labels:
          matchLabels:
            power: "true"
        target: balance-power
      - labels:
          matchLabels:
            special: "false"
        target: performance
```
