# Intel Power Manager

1. [Introduction](#introduction)
2. [Check the existence of sample power pods on the cluster](#check-the-existence-of-sample-power-pods-on-the-cluster)
3. [Obtain frequencies applied by each Power Profile](#obtain-frequencies-applied-by-each-Power-Profile)
4. [Obtain cores on which `balance-performance` Power Profile is applied](#obtain-cores-on-which-balance-performance-power-profile-is-applied)
5. [Check the frequencies on cores](#check-the-frequencies-on-cores)
6. [The Shared Profile](#the-shared-profile)
7. [C-States](#c-states)
8. [Uncore Frequency](#uncore-frequency)
9. [Time of Day](#time-of-day)
10. [Scaling Governors](#scaling-governors)
11. [Known limitations](#known-limitations)

---

## Introduction

Intel Power Manager is available for icx, spr, and clx architectures (you can find more about supported architectures in `generate_profiles` docs), and can be enabled in group vars.

After a successful deployment, the user can utilize special resources to manipulate cores' frequencies.
Sample pods can be deployed by setting `deploy_example_pods: true` in group vars and can be defined for each Power Node in specific host vars. 

The results of Power Manager work can be obtained in the following way:

## Check the existence of sample power pods on the cluster

```bash
kubectl get pods -n intel-power
NAME                                        READY   STATUS    RESTARTS   AGE
balance-performance-power-pod-node1         1/1     Running   0          122m
balance-power-power-pod-node1               1/1     Running   0          122m
controller-manager-765ccfd89b-m42q4         1/1     Running   0          123m
performance-power-pod-node1                 1/1     Running   0          122m
power-node-agent-qhz4g                      1/1     Running   0          123m
```

> NOTE: output may be different depending on the number of nodes and requested Power Profiles.

Three pods, one for each profile, were deployed. Let's stick to `balance-performance-power-pod-node1`.

# Obtain frequencies applied by each Power Profile

```bash
kubectl get PowerNodes -A -o yaml
```

## Obtain cores on which `balance-performance` Power Profile is applied

```bash
kubectl get PowerWorkloads -n intel-power balance-performance-node1 -o yaml
apiVersion: power.intel.com/v1
kind: PowerWorkload
metadata:
  creationTimestamp: "2023-12-12T10:56:12Z"
  generation: 2
  name: balance-performance-node1
  namespace: intel-power
  resourceVersion: "8030"
  uid: 6740161f-45e2-461d-ad41-063f6336b367
spec:
  name: balance-performance-node1
  powerProfile: balance-performance
  workloadNodes:
    containers:
    - exclusiveCpus:
      - 2
      - 74
      id: containerd://31d40cf10a653f073bffb4fec6456e79be60fac4d838407272188e53e1d66fb8
      name: balance-performance-container
      pod: balance-performance-power-pod-node1
      powerProfile: balance-performance
    cpuIds:
    - 2
    - 74
    name: node1
```

> > NOTE: The cores may differ on your machine.

`balance-performance` Power Profile is applied to core numbers 2 and 74

You can also check all assigned cores in your Power Nodes with the following command:

```bash
kubectl get PowerNodes -A -o yaml
```

## Check the frequencies on cores

```bash
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_max_freq
2825000
cat /sys/devices/system/cpu/cpu2/cpufreq/scaling_min_freq
2625000
cat /sys/devices/system/cpu/cpu74/cpufreq/scaling_max_freq
2825000
cat /sys/devices/system/cpu/cpu74/cpufreq/scaling_min_freq
2625000
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

## C-States

C-States can be set in host_vars for each node by setting cstates.enabled to true. User can choose to change C-states for Shared Pool, specific PowerProfile or even specific core.

## Uncore Frequency

Uncore frequency can be configured on a system-wide, per-package and per-die level, again in host_vars for each node by setting uncore_frequency.enabled to true.

## Time of Day

Time of Day can be configured in host_vars by setting time_of_day.enabled to true. Currently, there is known limitation that there can only exist one time of day schedule in the cluster, so please note, that only first schedule in cluster will be applied.

## Scaling Governors

Scaling governors first need to have scaling driver configured in host_vars for each node. For choosing specific scaling governor, user can either set up global scaling governor in group_vars, or local scaling governor in host_vars.

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

Shared Workload **may not** obtain all available cores, but will grab ones from the default pool if other profiles released them.
