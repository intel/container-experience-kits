# CNF Validation - Initially only test of SR-IOV count and mapping into CNF pod

## Summary

Script for testing environment to check how many SR-IOV VFs are used by deployed CNF pod and that those were mapped to the pod. These scripts were not designed and hardened to run in end user environment.

## Prerequisites

Kubernetes cluster with properly configured SR-IOV Device Plugin, configMap and CNI.

### For Docker-based version

Docker accessible for user.

### For Linux-based version

Study Dockerfile for details on required tools (jq, Robot framework...).

### Assumptions on CNF

Can be deployed with single command (which can be script that uses other commands).

## Configuration

Set environment variable KUBECONFIG to point to your Kubernetes configuration file that kubectl in Docker container will use.

Check config.json configuration options for validation.sh and test case details.

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
./validate.sh [--debug]
```

--debug forces debug option even if config.json has "debug": false .

### Linux-based version

Instead of run.sh , do

```
cd image
```

then follow Usage like above.

### Example run

```
~ $ ./validate.sh
{
  "CNFValidation": [
    {
      "name": "podCheckSRIOV",
      "description": "SR-IOV pod count, node count and env var check",
      "pass": true,
      "debug": "sriovName=intel.com/intel_sriov_odu; podCountSRIOV=4; nodeName=name1, beforeCountSRIOV=0, afterCountSRIOV=4; containerName=sriovtest1, PCIDEVICE_INTEL_COM_INTEL_SRIOV_ODU=0000:4b:0a.0,0000:4b:0a.3; containerName=sriovtest2, PCIDEVICE_INTEL_COM_INTEL_SRIOV_ODU=0000:4b:0a.2,0000:4b:0a.1;"
    }
  ],
  "timeStamps": {
    "start": "Wed May 17 11:12:32 UTC 2023",
    "stop": "Wed May 17 11:12:48 UTC 2023"
  }
}
```

### Manually deleting namespace

If pod is left hanging after testing with k8s/1-sriov-test-pod.yaml:

```
kubectl delete -f k8s/0-ns.yaml
```

## Tested

Tested on:

* Kubernetes setup as per https://hub.docker.com/r/intel/flexran_vdu on Ubuntu 22.04 on server with Intel Xeon Scalable processors and Intel Ethernet Controller XL710.
* Intel Network and Edge Container Bare Metal Reference System Architecture on Ubuntu 22.04RT with Access profile based on Intel Xeon Scalable processors and Intel Ethernet Controller E810.

## Current limitations

It can check only for one SR-IOV device name.

