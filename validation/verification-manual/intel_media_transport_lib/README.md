# Run sample workloads using Intel Media Transport Library

Following instructions can be used to run automted test cases using loopback test on 1 System.

All other available tests, including scenarios running workload between 2 Systems, and how to run them can be found at: <https://github.com/OpenVisualCloud/Media-Transport-Library/blob/main/doc/run.md#5-run-the-sample-application> (starting at step 5)

In case of any error, please check provided FAQ at: <https://github.com/OpenVisualCloud/Media-Transport-Library/blob/main/doc/run.md#8-faqs>

## 1. Test Preparation

For stress test run, 2 VFs binded to vfio-pci driver created from active PF are needed.
Following steps can be used for preparation of VFs on RA deployment with other SRIOV related features deployed.

1.1 Get info about available interfaces

```bash
dpdk-devbind.py -s
```

```log
Network devices using DPDK-compatible driver
============================================
0000:17:01.0 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
0000:17:01.5 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
0000:17:11.0 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
0000:17:11.1 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
0000:17:11.2 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
0000:17:11.3 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf

Network devices using kernel driver
===================================
0000:17:00.0 'Ethernet Controller E810-C for QSFP 1592' if=ens259f0 drv=ice unused=vfio-pci *Active*
0000:17:00.1 'Ethernet Controller E810-C for QSFP 1592' if=ens259f1 drv=ice unused=vfio-pci
0000:17:01.1 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v1 drv=iavf unused=vfio-pci *Active*
0000:17:01.2 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v2 drv=iavf unused=vfio-pci *Active*
0000:17:01.3 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v3 drv=iavf unused=vfio-pci *Active*
0000:17:01.4 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v4 drv=iavf unused=vfio-pci *Active*
0000:17:01.6 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v6 drv=iavf unused=vfio-pci *Active*
0000:17:01.7 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v7 drv=iavf unused=vfio-pci *Active*
0000:31:00.0 'BCM57416 NetXtreme-E Dual-Media 10G RDMA Ethernet Controller 16d8' if=ens787f0np0 drv=bnxt_en unused=vfio-pci
0000:31:00.1 'BCM57416 NetXtreme-E Dual-Media 10G RDMA Ethernet Controller 16d8' if=ens787f1np1 drv=bnxt_en unused=vfio-pci
0000:ca:00.0 'I350 Gigabit Network Connection 1521' if=ens803f0 drv=igb unused=vfio-pci *Active*
0000:ca:00.1 'I350 Gigabit Network Connection 1521' if=ens803f1 drv=igb unused=vfio-pci
0000:ca:00.2 'I350 Gigabit Network Connection 1521' if=ens803f2 drv=igb unused=vfio-pci
0000:ca:00.3 'I350 Gigabit Network Connection 1521' if=ens803f3 drv=igb unused=vfio-pci
```

1.2 Find an active E810 card PF

In example log above, the card PF is found at following line:

```log
0000:17:00.0 'Ethernet Controller E810-C for QSFP 1592' if=ens259f0 drv=ice unused=vfio-pci *Active*
```

1.3 Find 2 VFs binded to vfio-pci driver created from selected PF

__NOTE:__ when SRIOV operator is enabled in deployment, current VFs already binded to vfio-pci cannot be used as they are reserved by operator. In that case, use step 1.3.1 to rebind 2 Vfs from iavf to vfio-pci driver.

From log in step 1.1, VFs present in system from selected PF are:

```log
Network devices using DPDK-compatible driver
============================================
0000:17:01.0 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
0000:17:01.5 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf

Network devices using kernel driver
===================================
0000:17:01.1 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v1 drv=iavf unused=vfio-pci *Active*
0000:17:01.2 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v2 drv=iavf unused=vfio-pci *Active*
0000:17:01.3 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v3 drv=iavf unused=vfio-pci *Active*
0000:17:01.4 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v4 drv=iavf unused=vfio-pci *Active*
0000:17:01.6 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v6 drv=iavf unused=vfio-pci *Active*
0000:17:01.7 'Ethernet Adaptive Virtual Function 1889' if=ens259f0v7 drv=iavf unused=vfio-pci *Active*
```

Following VFs are binded to vfio-pci driver:

```log
0000:17:01.0 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
0000:17:01.5 'Ethernet Adaptive Virtual Function 1889' drv=vfio-pci unused=iavf
```

1.3.1 Rebind 2 VFs to vfio-pci driver for test

From list of VFs binded to iavf driver, let's choose VFs '0000:17:01.6' and '0000:17:01.7' for rebind.

First, remove active link of both interfaces:

```bash
ip link set ens259f0v6 down
ip link set ens259f0v7 down
```

Then, rebind VFs to vfio-pci driver:

```bash
dpdk-devbind.py -b vfio-pci 0000:17:01.6 0000:17:01.7
```

1.4 Save two VFs Bus IDs usd for test

```bash
export CARD_VF1="0000:17:01.6"
export CARD_VF2="0000:17:01.7"
```

## 2. Test Run

Execute following command to run sample workload using automated test cases included in imtl source :

```bash
/opt/cek/imtl/build/tests/KahawaiTest --p_port "${CARD_VF1}" --r_port "${CARD_VF2}"
```

Test will take approximately 15 mins. After it's finished, the output at the end should state "PASSED":

```log
[----------] Global test environment tear-down
[==========] 508 tests from 25 test suites ran. (808847 ms total)
[  PASSED  ] 508 tests.
st_plugin_free, succ with st22 sample plugin
```

__NOTE:__  Test suite is quite stressful, so randomly some small number of tests can fail.
