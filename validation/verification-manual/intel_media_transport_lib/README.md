# Run sample workloads using Intel Media Transport Library

Following instructions can be used to run automted test cases using loopback test on 1 System.

All other available tests, including scenarios running workload between 2 Systems, and how to run them can be found at: <https://github.com/OpenVisualCloud/Media-Transport-Library/blob/main/doc/run.md#5-run-the-sample-application> (starting at step 5)

In case of any error, please check provided FAQ at: <https://github.com/OpenVisualCloud/Media-Transport-Library/blob/main/doc/run.md#8-faqs>

## 1. Test Preparation

1.1 Get Card bus info of any E810 Card

```bash
lshw -c network -businfo
```

```log
Bus info          Device       Class          Description
=========================================================
pci@0000:17:00.0  ens259f0     network        Ethernet Controller E810-C for QSFP
pci@0000:17:00.1  ens259f1     network        Ethernet Controller E810-C for QSFP
```

1.2 Save bus ID of Card that will be used for test

```bash
export CARD_PF = "0000:17:00.0"
```

1.3 Create VFs for test

```bash
cd /opt/cek/imtl
./script/nicctl.sh create_vf "${CARD_PF}"
```

```log
0000:17:00.0 'Ethernet Controller E810-C for QSFP 1592' if=ens259f0 drv=ice unused=vfio-pci *Active*
Bind 0000:17:01.0(ens259f0v0) to vfio-pci success
Bind 0000:17:01.1(ens259f0v1) to vfio-pci success
Bind 0000:17:01.2(ens259f0v2) to vfio-pci success
Bind 0000:17:01.3(ens259f0v3) to vfio-pci success
Bind 0000:17:01.4(ens259f0v4) to vfio-pci success
Bind 0000:17:01.5(ens259f0v5) to vfio-pci success
Create VFs on PF bdf: 0000:17:00.0 ens259f0 succ
```

1.4 Save two VFs Bus IDs usd for test

```bash
export CARD_VF1 = "0000:17:01.0"
export CARD_VF2 = "0000:17:01.1"
```

## 2. Test Run

Execute following command to run sample workload using automated test cases included in imtl source :

```bash
./build/tests/KahawaiTest --p_port "${CARD_VF1}" --r_port $"{CARD_VF2}"
```

Test will take approximately 15 mins. After it's finished, the output at the end should state "PASSED":

```log
[----------] Global test environment tear-down
[==========] 508 tests from 25 test suites ran. (808847 ms total)
[  PASSED  ] 508 tests.
st_plugin_free, succ with st22 sample plugin
```

## 3. Test Teardown

3.1 Remove VFs created:

```bash
./scripts/nicctl.sh disable_vf "${CARD_PF}"
```
