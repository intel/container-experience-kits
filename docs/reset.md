# Reset

- [Reset](#Reset)
  - [Intro](#Intro)
  - [Execution](#Execution)
    - [Full cluster reset](#Full-cluster-reset)
    - [Uninstallation of the individual components](#Uninstallation-of-the-individual-components)
  - [Limitations and known issues](#Limitations-and-known-issues)

## Intro

It is possible to revert changes made by this set of playbooks to the target servers. Full cluster reset consists of three parts:
1. Removal of the Intel Container Experience Kits software installed on top of the Kubernetes cluster.
2. Reset of the Kubernetes cluster using Kubespray's `reset.yml` playbook.
3. Reset of the changes made in the host OS configuration, such as kernel flags or proxy configuration.

## Execution

> Note: It is strongly recommended to use the same inventory and vars files that were used for the cluster deployment.

### Full cluster reset

This will perform all reset stages listed in the [Intro](#Intro). Please execute below command:
```
ansible-playbook -i inventory.ini playbooks/reset.yml
```

### Uninstallation of the individual components

All tasks in the roles for state resetting are tagged, which means it's possible to uninstall selected components only. For example, to remove NFD only, this command can be executed:
```
ansible-playbook -i inventory.ini playbooks/reset.yml --tags=nfd
```
Tags can be combined to remove multiple features at once, for example, to remove NFD and CMK, use this command:
```
ansible-playbook -i inventory.ini playbooks/reset.yml --tags=nfd,cmk
```

Feature | Tag
--- | ---
Node Feature Discovery | `nfd`
Intel CPU Manager for Kubernetes | `cmk`
Intel QAT Device Plugin | `qat`
Intel GPU Device Plugin | `gpu`
Intel Device Plugins common files | `intel-dp`
Intel SRIOV Network Device Plugin | `sriov-dp`
Intel SR-IOV CNI Plugin | `sriov-cni`
Intel Userspace CNI Plugin (+OVS-DPDK and VPP) | `userspace`
Kubernetes node changes (host config) | `node`
Kubernetes master node changes (host config) | `master`
Kubespray (Kubernetes components) | `kubespray`

There are also 2 special extra _parent_ tags that remove multiple features at once:
- `intel`: equals to `nfd,cmk,qat,gpu,intel-dp,sriov-dp,sriov-cni,userspace`
- `infra`: equals to `master,node`

Example usage:
```
ansible-playbook -i inventory.ini playbooks/reset.yml --tags=intel
```

## Limitations and known issues

Removal of some of the features works in the best effort mode. This means that there may be some leftovers after running reset playbooks. This includes, but is not limited to:
- i40e and i40evf are not downgraded to their original version if an update was performed during the cluster deployment
- Linux kernel version isn't downgraded to the original version
- NFD node labels
- Node capacities (custom resources) added by CMK and Device Plugins
- Kubespray reset doesn't clean up proxy settings it added to the yum/apt configuration
