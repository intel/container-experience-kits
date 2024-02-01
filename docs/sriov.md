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

First set of variables enables SRIOV for selected network adapters, by setting `iommu_enabled` as `true` and passing names of the physical function interfaces. There's also an option to define how many virtual functions should be created for each physical function. In below example dataplane_interfaces configuration will create 6 VFs for 18:00.0 PF interface (PF0) and 4 VFs for 18:00.1 PF interface (PF1). VFs will be attached to default driver defined via 'default_vf_driver'. In our case to 'iavf' driver for PF0 and to 'vfio_pci' driver for PF1. If you need to assign different driver to specific VFs then 'sriov_vfs' section is used. It contains list of pairs vf_name and required driver. In our case VFs vf_00 and vf_05 are attached to 'vfio_pci' driver for PF0. PF1 does not require any specific driver, so 'sriov_vfs' section contains empty list. Name of the first VF is 'vf_00', the second VF has name 'vf_01' and so on. Name of the last VF is derived from 'sriov_numvfs - 1'. In our case 'vf_05'. So, for PF0 VFs devices names are vf_00-vf_05, 6 devices in total. This configuration will also add IOMMU kernel flags, and as a result will reboot the target worker node during deployment.
```
dataplane_interfaces:
  - bus_info: "18:00.0"
    sriov_numvfs: 6
    default_vf_driver: "iavf"
    sriov_vfs:
      vf_00: "vfio-pci"
      vf_05: "vfio-pci"
  - bus_info: "18:00.1"
    sriov_numvfs: 4
    default_vf_driver: "vfio-pci"
    sriov_vfs: []
```

`dataplane_interfaces` can be also configured automatically. All compatible NICs will be discovered and configured. Default VF driver is `iavf`, which can be changed by modifying `dataplane_interface_default_vf_driver`. Amount of VFs will be configured to maximum available on your NIC.

```
dataplane_interface_default_vf_driver: "iavf"
dataplane_interfaces: []
```

Next option defines whether the SRIOV CNI plugin will be installed on the target worker node. Setting it to `true` will cause the Ansible scripts to build and install SRIOV CNI plugin in the `/opt/cni/bin` directory on the target server.
```
sriov_cni_enabled: true`
```

Please refer to the [SRIOV Network Device Plugin](https://github.com/intel/sriov-network-device-plugin) and [SRIOV CNI documentation](https://github.com/intel/sriov-cni) to get more details about sriov resources and usage examples.
