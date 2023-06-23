*** Settings ***
Library           OperatingSystem
Library           JSONLibrary
Library           String
Resource          common.robot

*** Keywords ***

Create And Check SRIOV-dpdk-pod
    FOR    ${node}    IN    @{bmra_nodes}
        ${sriov_netdevice}=    Run Keyword    Get sriov netdevice   ${node}
        Should Not Be Empty   ${sriov_netdevice}   msg='Does not have sriov netdevice on node ${node}'
    END
    ${rc}=    Run And Return RC    awk -vD=${sriov_netdevice} ' { gsub("intel.com/intel_sriov_netdevice",D,$0); print $0; } ' < ../resources/yaml/sriov-dpdk-pod.yaml > sriov-dpdk-pod.yaml
    Should Be Equal    ${rc}    ${0}
    Sleep   1s
    ${rc}=    Run And Return RC    kubectl apply -f sriov-dpdk-pod.yaml
    Should Be Equal    ${rc}    ${0}
    Run Keyword    Check If POD Is Running And Get Return Status    sriov-dpdk-pod
    ${dpdkpod_env}=    Run    kubectl exec -it sriov-dpdk-pod -- env
    log    ${dpdkpod_env}
    ${dpdkpod_env_check}=    Run    kubectl exec -it sriov-dpdk-pod -- env | grep 'PCIDEVICE_INTEL_COM'
    ${pre}    ${vfs}=    Split String    ${dpdkpod_env_check}    =    1
    ${v1}    ${v2}=    Split String    ${vfs}    ,    1
    ${vf1}=    Get Substring    ${v1}    5
    ${vf2}=    Get Substring    ${v2}    5
    FOR    ${node}    IN    @{bmra_nodes}
        ${result}    Run Keyword And Return Status    Check If DPDK Pod VF Is Correct On Node    ${node}    ${vf1}    ${vf2}
        Run Keyword If    '${result}' == 'False'    Check if SRIOV-dpdk-pod Is Running    ${node}
    END

Check if SRIOV-dpdk-pod Is Running
    [Arguments]    ${node}
    ${stdout}=    Run    python /usr/src/dpdk-19.11.6/usertools/dpdk-devbind.py -s | grep "Network devices using DPDK-compatible driver" -A 3|grep "Virtual Function"
    Should Not Be Equal    ${stdout}    ${0}

NP SRIOV DPDK Test Teardown
    Run Keyword    Delete resource accord to yaml file    sriov-dpdk-pod.yaml

Check If DPDK Pod VF Is Correct On Node
    [Arguments]    ${node}    ${vf1}    ${vf2}
    ${VF_info}=    Run    lspci -nn |grep Eth | grep 'Virtual Function'
    log    ${VF_info}
    ${rc1}=    Run And Return RC    lspci -nn |grep Eth | grep 'Virtual Function'| awk '{print $1}' | grep ${vf1}
    ${rc2}=    Run And Return RC    lspci -nn |grep Eth | grep 'Virtual Function'| awk '{print $1}' | grep ${vf2}
    Should Be Equal    ${rc1}    ${0}
    Should Be Equal    ${rc2}    ${0}

