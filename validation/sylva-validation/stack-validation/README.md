# Stack Validation

## Summary

Scripts for testing environment to validate if desired Kubernetes features were activated and available to pods. These scripts were not designed and hardened to run in end user environment.

## Prerequisites

### Connectivity

Connectivity to Docker Hub is required to be able to load Alpine image. If connectivity is not available in your environment, then point k8s/*.yaml image: to your repository with Alpine image.

validatePhysicalStorage test and multi pod will download pci.ids file from internet. As needed, in k8s/multi.yaml add environment variable for http_proxy. Alternatively, as per k8s/multi.yaml build your own similar multi pod based on Alpine with added pci.ids or full pciutils.

Depending on speed of your connectivity, consider adjusting config.json podPause and k8s/multi.yaml wget timeout.

### For Docker-based version

Docker accessible for user.

### Prerequisites for Linux-based version

Study Dockerfile for details on required tools (jq, Robot framework...).

## Configuration

Set environment variable KUBECONFIG to point to your Kubernetes configuration file that kubectl in Docker container will use.

Check config.json configuration options for validation.sh and test case details.

Note when using pod security policies: validateHugepages uses pods with IPC_LOCK. validateSystemResourceReservation uses pods with hostPID. See below "Warnings on OpenShift".

## Building Docker image

Use script build.sh or do similar.

```
./build.sh
```

## Usage

### Docker version

Use script run.sh or do similar.

```
export KUBECONFIG=~/.kube/config  # or other location where kube config file is
./run.sh
```

Will start Docker container, then in it do:

```
./validate.sh [--only <testName>] [--debug]
```

--debug forces debug option even if config.json has "debug": false .

```
cd robot/tests
robot rc2.robot
```

### Linux-based version

Instead of run.sh , do

```
cd image
```

then follow Usage like above.

## Example run with "debug": false in config.json

```
~ $ ./validate.sh
{
  "stackValidation": {
    "testCases": [
      {
        "name": "validateHugepages",
        "description": "Validate huge pages",
        "ra2Spec": "ra2.ch.001",
        "nodes": [
          {
            "name": "kind-control-plane",
            "types": [
              {
                "name": "2Mi",
                "pass": false
              },
              {
                "name": "1Gi",
                "pass": true
              }
            ]
          }
        ]
      },
      {
        "name": "validateSMT",
        "description": "Validate SMT",
        "ra2Spec": "ra2.ch.004",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validatePhysicalStorage",
        "description": "Validate physical storage with SSD",
        "ra2Spec": "ra2.ch.009",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validateStorageQuantity",
        "description": "Validate storage quantity",
        "ra2Spec": "ra2.ch.010",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validateVcpuQuantity",
        "description": "Validate vCPU quantity",
        "ra2Spec": "ra2.ch.011",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validateNFD",
        "description": "Validate NFD labels",
        "ra2Spec": "ra2.ch.018",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validateSystemResourceReservation",
        "description": "Validate system resource reservation",
        "ra2Spec": "ra2.k8s.008",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": false
          }
        ]
      },
      {
        "name": "validateCPUPinning",
        "description": "Validate CPU Manager",
        "ra2Spec": "ra2.k8s.009",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": false
          }
        ]
      },
      {
        "name": "validateLinuxDistribution",
        "description": "Validate Linux distribution for deb/rpm",
        "ra2Spec": "ra2.os.001",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validateLinuxKernelVersion",
        "description": "Validate Linux kernel version",
        "ra2Spec": "ra2.os.002",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validateKubernetesAPIs",
        "description": "Validate k8s APIs without alpha+beta or is exception",
        "ra2Spec": "ra2.k8s.012",
        "pass": true
      },
      {
        "name": "validateAnuketProfileLabels",
        "description": "Validate Anuket profile labels",
        "ra2Spec": "ra2.k8s.011",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true
          }
        ]
      },
      {
        "name": "validateSecurityGroups",
        "description": "Validate security groups with NetworkPolicy",
        "ra2Spec": "ra2.k8s.014",
        "pass": false
      }
    ]
  },
  "timeStamps": {
    "start": "Wed May 17 10:50:09 UTC 2023",
    "stop": "Wed May 17 10:51:42 UTC 2023"
  }
}
```

```
~ $ ./validate.sh --only validateVcpuQuantity --debug
{
  "stackValidation": {
    "testCases": [
      {
        "name": "validateVcpuQuantity",
        "description": "Validate vCPU quantity",
        "ra2Spec": "ra2.ch.011",
        "nodes": [
          {
            "name": "kind-control-plane",
            "pass": true,
            "debug": "vcpu=128"
          }
        ]
      }
    ]
  },
  "timeStamps": {
    "start": "Wed May 17 10:55:45 UTC 2023",
    "stop": "Wed May 17 10:55:45 UTC 2023"
  }
}
```

```
# cd robot/tests
# robot rc2.robot
==============================================================================
Rc2 :: RC2 Robot Framework selection
==============================================================================
BMRA NP Device Plugins SRIOV DPDK                                     | PASS |
------------------------------------------------------------------------------
Rc2 :: RC2 Robot Framework selection                                  | PASS |
1 test, 1 passed, 0 failed
==============================================================================
Output:  /path/to/stack-validation/robot/tests/output.xml
Log:     /path/to/stack-validation/robot/tests/log.html
Report:  /path/to/stack-validation/robot/tests/report.html
```

### Manually deleting pods

```
kubectl delete -f k8s/ns.yaml
```

## Test on (reference) Kind cluster

### Install

Install Kind as per https://github.com/kubernetes-sigs/kind .

```
kind create cluster
```

This will add required entries into ~/.kube/config .

```
kubectl label nodes kind-control-plane anuket.io/profile=basic
kubectl apply -k https://github.com/kubernetes-sigs/node-feature-discovery/deployment/overlays/default?ref=v0.12.1
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset.yml
```

### (Optional) Configure Huge Pages

```
sudo vi /etc/default/grub
```

to in line GRUB_CMDLINE_LINUX add "default_hugepagesz=1G hugepagesz=1G hugepages=4".

```
sudo bash
grub2-mkconfig -o /boot/grub2/grub.cfg
echo nodev /mnt/huge hugetlbfs pagesize=1GB 0 0 >> /etc/fstab
reboot
```

### Stop

```
docker kill kind-control-plane
docker rm kind-control-plane
```

## Test k3s cluster

### (Optional) Configure Huge Pages

Same as for above Kind cluster.

### Install

```
curl -sfL https://get.k3s.io | sudo INSTALL_K3S_SKIP_ENABLE=true sh -
```

### Start

In one shell do:

```
sudo K3S_KUBECONFIG_MODE=644 INSTALL_K3S_EXEC="--kubelet-arg cpu-manager-policy=static --kubelet-arg reserved-cpus=0-1  --kubelet-arg kube-reserved=memory=1Gi,ephemeral-storage=1Gi,pid=1000 --kubelet-arg system-reserved=memory=1Gi,ephemeral-storage=2Gi,pid=1000 --cluster-cidr=192.168.0.0/16" /usr/local/bin/k3s server --node-label anuket.io/profile=basic
```

In another shell do:

```
cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
kubectl apply -k https://github.com/kubernetes-sigs/node-feature-discovery/deployment/overlays/default?ref=v0.12.1
kubectl apply -f https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/master/deployments/multus-daemonset.yml
```

### Stop

Ctrl-C k3s process.

```
sudo /usr/local/bin/k3s-killall.sh
```

## Tested on

Various test cases were tested on worker nodes that are bare metal or in VMs, on servers with Intel Xeon Scalable Processors and Intel Ethernet, using these Kubernetes distributions and Linux:

* Kind v0.18.0 on worker node with CentOS 9 Stream
* k3s v1.26.4+k3s1 on CentOS 9 Stream
* Intel Network and Edge Container Bare Metal Reference System Architecture on Ubuntu 22.04RT
* Red Hat OpenShift 4.11.25 v1.24.6+5658434 on CoreOS
* AWS EKS v1.24.8-eks-ffeb93d on Amazon Linux 2 on EC2 c6i

### On OpenShift

Currently only the following validate.sh tests work: validateSMT, validateStorageQuantity, validateVcpuQuantity, validateNFD, validateKubernetesAPIs, validateLinuxKernelVersion, validateAnuketProfileLabels.

Other test cases require pods of which current images (using IPC_LOCK or hostPID) are not supported with default OpenShift pod security settings.
