# Intel(R) FlexRAN(TM) Readme
This document is about setting up and deploying the Intel® FlexRAN™ software2 as either containers in a POD or Bare Metal to be used as part of a 5G end-to-end setup, or in a stand-alone manner in Timer Mode and xRAN Mode using the Container Bare Metal Reference Architecture (BMRA) on a single 3th/4th Gen Intel® Xeon® Scalable processor-based platform with Intel® vRAN Boost.

A formal PDF Quick Start Guide for Intel(R) FlexRAN(TM) deployment using the RA playbooks is published at this URL:
<https://networkbuilders.intel.com/solutionslibrary/network-and-cloud-edge-reference-system-architecture-flexran-software-single-server-quick-start-guide>

## Hardware BOM
for ICX
- 1x 3th Gen Intel® Xeon® Scalable processors
- 1x Intel® Mount Bryce Card (acc100)
- Intel® Ethernet Network Adapter E810-CQDA2 or Intel® Ethernet Controller XL710

for SPR
- 1x 4th Gen Intel® Xeon® Scalable processors with embedded Intel® vRAN Boost(acc200)
- Intel® Ethernet Network Adapter E810-CQDA2 or Intel® Ethernet Controller XL710

## Software BOM
- OS:
    - Ubuntu22.04 5.15.0.1036-realtime kernel (for host and pod type)
    - Rhel9.2 5.14.0-284.11.1.rt14.296.el9_2.x86_64 realtime kernel (for host)
- Kubernetes: 1.27.1
- Container runtime: containerd 1.7.2
- FlexRAN: 23.07
- Intel® oneAPI Base Tookit: 2023.1.0
- DPDK: 22.11.1

## Deploy in Bare Metal (host type)
- Download the following files from the Intel® Developer Zone portal.
    - FlexRAN-23.07-L1.tar.gz_part0：https://cdrdv2.intel.com/v1/dl/getContent/784883
    - FlexRAN-23.07-L1.tar.gz_part1： https://cdrdv2.intel.com/v1/dl/getContent/784884
    - dpdk_patch-23.07.patch： https://cdrdv2.intel.com/v1/dl/getContent/784885
- Copy the FlexRAN™ software packages and merge them into one final package on Bare Metal.
    ```
    # mkdir -p /opt/cek/intel-flexran/
    # cat FlexRAN-23.07-L1.tar.gz_part0 FlexRAN-23.07-L1.tar.gz_part1 > FlexRAN-23.07.tar.gz
    # cd /opt/cek/intel-flexran/
    # tar -xvf FlexRAN-23.07.tar.gz
    # cat ReadMe.txt
    # ./extract.sh
    ```
- Copy the DPDK patch to Ansible Host.
    ```
    # mkdir -p /opt/patches/flexran/dpdk-22.11/
    # cp dpdk_patch-23.07.patch /opt/patches/flexran/dpdk-22.11/
    ```
- Ansible Host
    - Generate the configuration files for Access Profile.
        ```
        # export PROFILE=access
        # make k8s-profile PROFILE=${PROFILE} ARCH=spr ### ARCH can be icx or spr
        ```
    - Update the `inventory.ini` file to match the target server’s hostname.
    Note: For xRAN test mode on Bare Metal deployment, a separate oRU node is required.
    - Update the `host_vars/` filenames with the target machine's hostnames.
        ```
        # cp host_vars/node1.yml host_vars/<bbu hostname>.yml
        # cp host_vars/node1.yml host_vars/<oru hostname>.yml #Only in case of xRAN test mode in BM
        ```
    - Update `host_vars/<bbu_hostname>.yml` with PCI device information specific to the target servers. You need two PFs and a minimum of four VFs per PF.
        ```
        dataplane_interfaces:
        - bus_info: "18:00.0"
        pf_driver: "ice"   ### E810 PF driver
        default_vf_driver: "vfio-pci"
        sriov_numvfs: 4
        - bus_info: "18:00.1"
        pf_driver: "ice"
        default_vf_driver: "vfio-pci"
        sriov_numvfs: 4
        ```
    - Set the FlexRAN™ test mode in `group_vars/all.yml` as per your testing need
        ```
        intel_flexran_enabled: true # if true, deploy FlexRAN
        intel_flexran_type: "host"
        intel_flexran_mode: "timer" # supported values are "timer" and "xran"
        ```
    - Deploy
        ```
        # ansible-playbook -i inventory.ini playbooks/k8s/patch_kubespray.yml
        # ansible-playbook -i inventory.ini playbooks/access.yml
        ```
    - Validate FlexRAN™ software in Timer Mode
        - Terminal 1: run the FlexRAN™ software L1 app
            ```
            # cd /opt/cek/intel-flexran/
            # source set_env_var.sh -d
            # cd bin/nr5g/gnb/l1
            # ./l1.sh -e
            ```
        - Terminal 2: run the Test MAC app
            ```
            # cd /opt/cek/intel-flexran/
            # source set_env_var.sh -d
            # cd bin/nr5g/gnb/testmac
            # ./l2.sh --testfile=spr-sp-eec/sprsp_eec_mu0_10mhz_4x4_hton.cfg
            ```
    - Valite FlexRAN™ software in XRAN Mode
        - Terminal 1 on BBU server: run the FlexRAN™ software L1 app
            ```
            # cd /opt/cek/intel-flexran/
            # source set_env_var.sh -d
            # cd bin/nr5g/gnb/l1/orancfg/sub3_mu0_10mhz_4x4/gnb
            # ./l1.sh -oru
            ```
        - Terminal 2 on BBU server: run the Test MAC app
            ```
            # cd /opt/cek/intel-flexran/
            # source set_env_var.sh -d
            # cd bin/nr5g/gnb/testmac
            # ./l2.sh -- testfile=../l1/orancfg/sub3_mu0_10mhz_4x4/gnb/testmac_clxsp_mu0_10mhz_hton_oru.cfg
            ```
        - Terminal 3 on ORU server:
            ```
            # cd /opt/cek/intel-flexran/bin/nr5g/gnb/l1/orancfg/sub3_mu0_10mhz_4x4/oru
            # ./run_o_ru.sh
            ```

## Deploy in Container (pod type)
- Ansible Host
    - Generate the configuration files for Access Profile.
        ```
        # export PROFILE=access
        # make k8s-profile PROFILE=${PROFILE} ARCH=spr ### ARCH can be icx or spr
        ```
    - Update the `inventory.ini` file to match the target server’s hostname.
    - Update the `host_vars/` filenames with the target machine's hostnames.
        ```
        # cp host_vars/node1.yml host_vars/<bbu hostname>.yml
        ```
    - Update `host_vars/<bbu_hostname>.yml` with PCI device information specific to the target servers. You need two PFs and a minimum of four VFs per PF.
        ```
        dataplane_interfaces:
        - bus_info: "18:00.0"
        pf_driver: "ice"   ### E810 PF driver
        default_vf_driver: "vfio-pci"
        sriov_numvfs: 4
        - bus_info: "18:00.1"
        pf_driver: "ice"
        default_vf_driver: "vfio-pci"
        sriov_numvfs: 4
        ```
    - Set the FlexRAN™ test mode in `group_vars/all.yml` as per your testing need.
        ```
        intel_flexran_enabled: true # if true, deploy FlexRAN
        intel_flexran_type: "pod"
        intel_flexran_mode: "timer" # supported values are "timer" and "xran"
        ```
    - Set container runtime in `group_vars/all.yml`.
        ```
        #Note: Since FlexRAN 23.07, the default runtime for running FlexRAN is containerd to support non-root feature.
        container_runtime: containerd
        ```
    - We disable fec operator as we use sriov device plugin for enabling FEC device in this release.
        ```
        intel_sriov_fec_operator_enabled: false
        ```
    - Deploy
        ```
        # ansible-playbook -i inventory.ini playbooks/k8s/patch_kubespray.yml
        # ansible-playbook -i inventory.ini playbooks/access.yml
        ```
    - Validate FlexRAN™ software in Timer Mode
        - You can find the FlexRAN™ POD name using the below command:
            ```
            # kubectl get pods -A | grep flexran
              default        flexran-dockerimage-release    2/2     Running   0    10m
            ```
        - The status of the L1 app can be checked using the below command:
            ```
            # kubectl logs -f flexran-dockerimage-release -c flexran-l1app
            ```
        - The status of the L2 TestMAC app can be checked using the below command:
            ```
            # kubectl logs -f flexran-dockerimage-release -c flexran-testmac
            ```
    - Validate FlexRAN™ software in XRAN Mode
        - You can find the FlexRAN™ POD name using the below command:
            ```
            # kubectl get pods -A | grep flexran
              default        flexran-vdu      1/1     Running   0      91m
              default        flexran-vru      1/1     Running   0      91m
            ```
        - Terminal 1: run the FlexRAN™ software L1 app
            ```
            # kubectl exec -it flexran-vdu -- bash
            # cd flexran/bin/nr5g/gnb/l1/spree_oran_tests/sub3_mu0_20mhz_4x4/gnb/
            # ./l1.sh -oru
            ```
        - Terminal 2: run the Test MAC app
            ```
            # kubectl exec -it flexran-vdu -- bash
            # cd flexran/bin/nr5g/gnb/testmac
            # ./l2.sh --testfile=../l1/spree_oran_tests/sub3_mu0_20mhz_4x4/gnb/testmac_spree_mu0_20mhz_hton_oru.cfg
            ```
        - Terminal 3: run ORU
            ```
            # kubectl exec -it flexran-vru -- bash
            # cd flexran/bin/nr5g/gnb/l1/spree_oran_tests/sub3_mu0_20mhz_4x4/oru/
            Note: update the file run_o_ru.cfg for the port BDF corresponding with your server port BDF, example <--vf_addr_o_xu_a "0000:ca:11.0,0000:ca:11.1">
            # ./run_o_ru.sh
            ```
