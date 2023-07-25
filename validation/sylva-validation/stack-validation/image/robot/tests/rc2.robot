*** Settings ***
Documentation     RC2 Robot Framework selection
Suite Setup       Get Machine Info 2
Library           Collections
Resource          ../keywords/common.robot
Resource          ../keywords/bmra_onprem.robot

*** Test Cases ***

BMRA NP Device Plugins SRIOV DPDK
    [Timeout]    1 minutes
    [Tags]    SRIOV
    Run Keyword    Create And Check SRIOV-dpdk-pod
    [Teardown]    NP SRIOV DPDK Test Teardown
