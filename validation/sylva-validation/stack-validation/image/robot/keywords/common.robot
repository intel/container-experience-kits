*** Settings ***
Library           OperatingSystem
Library           String
Library           JSONLibrary
Library           json

*** Keywords ***
Get Machine Info 2
    ${nodes} =    Run    kubectl get no -o json | jq -r '.items[].metadata.name'
    ${bmra_nodes} =    Split String    ${nodes}
    Set Suite Variable   ${bmra_nodes}

Check if All Pods Is Running
    ${pod_all_status}=    Execute Command    kubectl get pod -A
    log    ${pod_all_status}
    ${pod_no}=    Execute Command    kubectl get pod -A | grep -v STATUS | grep -v Running | grep -v Completed | grep -v Evicted | awk '{print $2}'
    ${pods}=    Split To Lines    ${pod_no}
    FOR    ${pod}    IN    @{pods}
        Check If POD Is Running And Get Return Status    ${pod}
    END

Check If POD Is Running And Get Return Status
    [Arguments]    ${pod}
    ${result}=    Run Keyword And Return Status    Wait Until Keyword Succeeds    5 min    30 sec    Check if Pod Is Running    ${pod}
    Run Keyword If    '${result}' == 'False'    Some pods Is Not Running    ${pod}
    RETURN    ${result}

Check if Pod Is Running
    [Arguments]    ${pod_name}
    ${stdout}=    Run    kubectl get pods -A | grep ${pod_name} | awk '{print $4}'
    Should Match Regexp    ${stdout}    (.*Running.*|.*Completed.*)

Delete resource accord to yaml file
    [Arguments]    ${yaml_file}
    Run    kubectl delete -f ${yaml_file} --force

Delete Pod Mandatory
    [Arguments]    ${pod_name}
    SSH Login BMRA Master
    ${rc}=    Execute Command    kubectl get pod | grep ${pod_name}    return_stdout=False    return_rc=True
    Run Keyword If    ${rc} == 0    Execute Command    kubectl delete pod ${pod_name} --grace-period=0 --force
    ...    ELSE    Pass Execution

Get sriov netdevice
    [Arguments]    ${node_name}
    ${sriov_alloc} =    Run    kubectl get no ${node_name} -o json | jq -r '.status.allocatable | to_entries | .[] | select(.key | match("sriov")) | .key ' | head -1
    Return From Keyword    ${sriov_alloc}

