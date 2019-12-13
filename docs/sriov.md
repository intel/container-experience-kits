# SRIOV Network Device Plugin and SRIOV CNI plugin

## Cluster configuration options

In order to install SRIOV Network Device Plugin set `sriov_net_dp_enabled` value to `true` in your group vars file. Setting it to `false` will disable SRIOV Network Device Plugin installation and cause other related options to be ignored.
```
sriov_net_dp_enabled: true
```

You can also change the Kubernetes namespace used for the plugin deployment - by default it's `kube-system`.
```
sriov_net_dp_namespace: kube-system
```

It's possible to build and store image locally or use one from public external registry. If you want to use image from the Docker Hub (recommended and faster option), please use `false`.
```
sriov_net_dp_build_image_locally: false
```

The `example_net_attach_defs` dictionary allows for enabling/disabling automatic creation of example net-attach-def objects. If you want to create the example net-attach-def resource for use with the SRIOV Network Device Plugin and SRIOV CNI, please set below variable to `true`.
```
example_net_attach_defs:
  sriov_net_dp: true
```

## Worker node specific options

There's also a set of configuration options that are applied in per-node manner.

First set of variables enables SRIOV for selected network adapters, by setting `sriov_enabled` as `true` and passing names of the physical function interfaces. There's also an option to define how many virtual functions should be created for each physical function. In below example `sriov_nics` configuration will create 4 VFs for enp175s0f0 PF interface and attach them to vfio-pci driver and 2 VFs for enp175s0f1 PF interface and attach them to kernel mode iavf driver. It will also add IOMMU kernel flags, and as a result will reboot the target worker node during deployment.
```
sriov_nics:
  - name: enp175s0f0
    sriov_numvfs: 4
    vf_driver: vfio-pci
  - name: enp175s0f1
    sriov_numvfs: 2
    vf_driver: iavf
```

Next option defines whether the SRIOV CNI plugin will be installed on the target worker node. Setting it to `true` will cause the Ansible scripts to build and install SRIOV CNI plugin in the `/opt/cni/bin` directory on the target server.
```
sriov_cni_enabled: true`
```

If `sriov_net_dp_enabled` is set to `true` in all.yml (group vars), plase adjust and uncomment below configuration in the node host vars file. Below dictionary will be used to prepare and apply SRIOV Network Device Plugin configuration.
In the example below we use PF names of the interfaces that we enabled SRIOV for in the above example. Then we define driver bindings for each of them. Below configuration means that all VFs that belong to the `enp175s0f0` interface will be bound to the i40evf driver and will be available for kernel datapath use (netdevice mode). VFs created on `enp175s0f1` and `enp175s0f2` will be attached to the userspace vfio-pci and igb_uio drivers respectively, which will make them available for use with the userspace dataplane applications. This configuration will also cause assignment of VFs to appropriate resource pools in the SRIOV Network Device Plugin: `intel_sriov_netdevice` for the `enp175s0f0` VFs and `intel_sriov_dpdk` for the `enp175s0f1` VFs.
```
sriov_net_dp_config:
- pfnames: ["enp175s0f0"]     # PF interface names - their VFs will be attached to specific driver
  driver: "i40evf"            # available options:  "i40evf", "vfio-pci", "igb_uio"
- pfnames: ["enp175s0f1"]     # PF interface names - their VFs will be attached to specific driver
  driver: "vfio-pci"          # available options:  "i40evf", "vfio-pci", "igb_uio"
- pfnames: ["enp175s0f2"]     # PF interface names - their VFs will be attached to specific driver
  driver: "igb_uio"           # available options:  "i40evf", "vfio-pci", "igb_uio"
```

Please refer to the [SRIOV Network Device Plugin](https://github.com/intel/sriov-network-device-plugin) and [SRIOV CNI documentation](https://github.com/intel/sriov-cni) to get more details and usage examples.