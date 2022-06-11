# Check Node Feature Discovery
Node Feature Discovery (NFD) lists platform capabilities and can be used for intelligent scheduling of workloads in Kubernetes.

To verify that NFD in Kubernetes is running as expected, use the following command:
```
# kubectl get ds --all-namespaces | grep node-feature-discovery
kube-system node-feature-discovery-worker      1    1    1    1    1    <none>    61m
```

To view the Kubernetes node labels created by NFD:
```
# kubectl label node --list –-all
Listing labels for Node./node1:
 feature.node.kubernetes.io/pci-0300_1a03.present=true
 feature.node.kubernetes.io/cpu-rdt.RDTCMT=true
 feature.node.kubernetes.io/cpu-pstate.status=active
 feature.node.kubernetes.io/kernel-config.NO_HZ=true
 feature.node.kubernetes.io/cpu-cpuid.FMA3=true
 feature.node.kubernetes.io/cpu-cpuid.AVX2=true
 feature.node.kubernetes.io/kernel-config.NO_HZ_FULL=true
 feature.node.kubernetes.io/cpu-cpuid.STIBP=true
 feature.node.kubernetes.io/cpu-cpuid.ADX=true
 feature.node.kubernetes.io/cpu-rdt.RDTMON=true
 kubernetes.io/arch=amd64
 feature.node.kubernetes.io/system-os_release.VERSION_ID=8.5
 feature.node.kubernetes.io/memory-numa=true
 feature.node.kubernetes.io/cpu-cpuid.SHA=true
 feature.node.kubernetes.io/intel.sgx=true
 feature.node.kubernetes.io/kernel-version.major=4
 feature.node.kubernetes.io/cpu-cpuid.AVX512VL=true
 feature.node.kubernetes.io/system-os_release.VERSION_ID.major=8
 sgx.configured=true
 feature.node.kubernetes.io/kernel-version.revision=0
 feature.node.kubernetes.io/cpu-cpuid.AVX=true
 feature.node.kubernetes.io/cpu-cpuid.AESNI=true
 feature.node.kubernetes.io/cpu-rdt.RDTL3CA=true
 feature.node.kubernetes.io/cpu-cpuid.VAES=true
 feature.node.kubernetes.io/cpu-cpuid.AVX512VNNI=true
 feature.node.kubernetes.io/cpu-sgx.enabled=true
 feature.node.kubernetes.io/cpu-cpuid.AVX512CD=true
 feature.node.kubernetes.io/cpu-cpuid.VPCLMULQDQ=true
 feature.node.kubernetes.io/network-sriov.capable=true
 feature.node.kubernetes.io/pci-1200_8086.sriov.capable=true
 feature.node.kubernetes.io/pci-1200_8086.present=true
 feature.node.kubernetes.io/cpu-cpuid.IBPB=true
 feature.node.kubernetes.io/cpu-cpuid.AVX512VPOPCNTDQ=true
 feature.node.kubernetes.io/network-sriov.configured=true
 storage=minio
 feature.node.kubernetes.io/cpu-cpuid.GFNI=true
 beta.kubernetes.io/arch=amd64
 feature.node.kubernetes.io/cpu-cpuid.WBNOINVD=true
 feature.node.kubernetes.io/system-os_release.ID=rhel
 feature.node.kubernetes.io/cpu-cpuid.AVX512BITALG=true
 feature.node.kubernetes.io/storage-nonrotationaldisk=true
 feature.node.kubernetes.io/cpu-pstate.scaling_governor=performance
 app=kmra
 feature.node.kubernetes.io/cpu-pstate.turbo=true
 feature.node.kubernetes.io/cpu-cpuid.AVX512DQ=true
 feature.node.kubernetes.io/cpu-cpuid.AVX512BW=true
 feature.node.kubernetes.io/kernel-version.full=4.18.0-348.el8.x86_64
 feature.node.kubernetes.io/cpu-cpuid.AVX512VBMI2=true
 kubernetes.io/hostname=node1
 feature.node.kubernetes.io/cpu-cpuid.AVX512VBMI=true
 feature.node.kubernetes.io/cpu-rdt.RDTMBA=true
 qat.configured=true
 feature.node.kubernetes.io/cpu-cpuid.VMX=true
 feature.node.kubernetes.io/pci-0b40_8086.sriov.capable=true
 feature.node.kubernetes.io/intel.qat=true
 feature.node.kubernetes.io/pci-0b40_8086.present=true
 feature.node.kubernetes.io/cpu-cstate.enabled=true
 feature.node.kubernetes.io/cpu-cpuid.AVX512F=true
 feature.node.kubernetes.io/cpu-hardware_multithreading=true
 kubernetes.io/os=linux
 beta.kubernetes.io/os=linux
 intel.power.node=true
 feature.node.kubernetes.io/kernel-version.minor=18
 feature.node.kubernetes.io/cpu-cpuid.AVX512IFMA=true
 feature.node.kubernetes.io/system-os_release.VERSION_ID.minor=5
 feature.node.kubernetes.io/cpu-rdt.RDTMBM=true
Listing labels for Node./controller:
 kubernetes.io/arch=amd64
 kubernetes.io/hostname=controller
 kubernetes.io/os=linux
 node-role.kubernetes.io/control-plane=
 node-role.kubernetes.io/master=
 node.kubernetes.io/exclude-from-external-load-balancers=
 beta.kubernetes.io/arch=amd64
 beta.kubernetes.io/os=linux
```
The node labels can be used when provisioning a pod. The provided pod manifest [pod-nfd.yml](pod-nfd.yml) can be used to test this. The pod is scheduled only if there is a node with QAT available. The content of the file is:
```
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-nfd-1
spec:
  nodeSelector:
    feature.node.kubernetes.io/custom-intel.qat: "true"
  containers:
  - name: pod-nfd-1
    image: ubuntu:focal
    command:
    - "/bin/bash"
    - "-c"
    args:
    - "tail -f /dev/null"
```
Deploy the pod:
```
# kubectl apply -f pod-nfd.yml
```
If no node is available that matches the nodeSelectors, the pod will remain in pending state.

