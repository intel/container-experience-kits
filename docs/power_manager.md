# Intel Power Manager 

1. [Introduction](#introduction)
2. [Check the existence of sample power pods on the cluster](#check-the-existence-of-sample-power-pods-on-the-cluster)
3. [Check the frequencies which will be set by `balance-performance` Power Profile](#check-the-frequencies-which-will-be-set-by-balance-performance-power-profile)
4. [Obtain cores on which `balance-performance` Power Profile is applied](#obtain-cores-on-which-balance-performance-power-profile-is-applied)
5. [Check the frequencies on cores](#check-the-frequencies-on-cores)
6. [The Shared Profile](#the-shared-profile)
7. [Known limitations](#known-limitations)

---

## Introduction

Intel Power Manager is available for icx, spr, and clx architectures (you can find more about supported architectures in `generate_profiles` docs), and can be enabled in group vars.

After a successful deployment, the user can utilize special resources to manipulate cores' frequencies.
Sample pods can be deployed by setting `deploy_example_pods: true` in group vars.

The results of Power Manager work can be obtained in the following way:

## Check the existence of sample power pods on the cluster

```bash
kubectl get pods -n intel-power
NAME                                 READY   STATUS    RESTARTS   AGE
balance-performance-power-pod        1/1     Running   0          21m
balance-power-power-pod              1/1     Running   0          21m
controller-manager-f584c9458-682p5   1/1     Running   0          16h
performance-power-pod                1/1     Running   0          21m
power-node-agent-8cxmp               2/2     Running   0          16h
```

> NOTE: output may be different depending on the number of nodes and requested Power Profiles.

Three pods, one for each profile, were deployed. Let's stick to `balance-performance-power-pod`.

## Check the frequencies which will be set by `balance-performance` Power Profile

```bash
kubectl get PowerProfiles -n intel-power balance-performance-node1 -o yaml
apiVersion: power.intel.com/v1alpha1
kind: PowerProfile
metadata:
  creationTimestamp: "2022-01-25T17:07:08Z"
  generation: 1
  name: balance-performance-node1
  namespace: intel-power
  resourceVersion: "17538"
  uid: 05599219-d042-4b9c-9bbf-42ef67effd24
spec:
  epp: balance_performance
  max: 2700
  min: 2500
  name: balance-performance-node1
```

> NOTE: The max/min frequencies may differ on your machine.

In `spec` the values max and min represent new frequencies that will be set to specific cores.

## Obtain cores on which `balance-performance` Power Profile is applied

```bash
kubectl get PowerWorkloads -n intel-power balance-performance-node1-workload -o yaml
apiVersion: power.intel.com/v1alpha1
kind: PowerWorkload
metadata:
  creationTimestamp: "2022-01-26T10:12:00Z"
  generation: 1
  name: balance-performance-node1-workload
  namespace: intel-power
  resourceVersion: "246287"
  uid: f8720a7e-f7b2-4f31-bf4f-2a38ad8a7c07
spec:
  name: balance-performance-node1-workload
  nodeInfo:
    containers:
    - exclusiveCpus:
      - 2
      - 66
      id: 495d5547a5211774e605c4a2ebe4b9fbcf44fbd056cc08e0847b68143627700a
      name: balance-performance-container
      pod: balance-performance-power-pod
      powerProfile: balance-performance-node1
    cpuIds:
    - 2
    - 66
    name: node1
  powerProfile: balance-performance-node1
```

> > NOTE: The cores may differ on your machine.

`balance-performance` Power Profile is applied to core numbers 2 and 66

You can also check all assigned cores in your Power Nodes with the following command:

```bash
kubectl get PowerNodes -A -o yaml
```

## Check the frequencies on cores

```bash
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_max_freq
2700000
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_min_freq
2500000
cat /sys/devices/system/cpu/cpu66/cpufreq/scaling_max_freq
2700000
cat /sys/devices/system/cpu/cpu66/cpufreq/scaling_min_freq
2500000
```

In comparison, the core that was not obtained by Power Workload has the following values:

```bash
cat /sys/devices/system/cpu/cpu22/cpufreq/scaling_max_freq
3500000
cat /sys/devices/system/cpu/cpu22/cpufreq/scaling_min_freq
800000
```

> NOTE: The frequencies may differ on your machine.

## The Shared Profile

The Shared Profile is a custom profile that can be defined by the user. It requires deploying the custom Shared Workload as well.
The main purpose of Shared Profile is to allow users to customization of core frequencies.

The Shared Profile has either a cluster-wide or single node impact. The Shared Workload is deployed per node, so the cores might be scaled.

**The user is responsible for setting the correct frequency values for Shared Profile. This cannot be checked in preflight!**

The resources for Shared Profile are not visible in allocatable kubelet resources as cores will be scaled as soon as Shared Workload is deployed.

## Known limitations

1. The Performance Power Profile

The CPUs with `CPU max MHz` lower than 3600 are not capable of successfully applying the `performance` Power Profile.
Despite the fact that Power Profile seems to be deployed and the Power Workload reserves the cores the frequencies will not be applied. 

To check if your machine is capable of using the `performance` Power Profile use the following command:

```bash
lscpu | grep "CPU max MHz"
CPU max MHz:                     3500.0000
```

You can see that this machine is not capable of utilizing the `performance` Power Profile.

2. The Shared Power Profile

More than one Shared Power Profile cannot be used on the same node. For example, it is not possible to use a global shared power profile configured in group vars and at the same time scale core with config for a specific node.

Shared Profile will grab all cores that are not marked as exclusive - please consider not deploying shared profile if special pods will need access to cores scaled via performance, balance-performance, or balance-power profiles.

Due to strong dependency on AppQoS the list for exclusive CPUs must not be empty even if there are no exclusive CPUs in the kubelet config at the moment. Please put the last core from the machine to the list of exclusive CPUs in host vars in that case.

Shared Workload **may not** obtain all available cores, but will grab ones from the default pool if other profiles released them.
