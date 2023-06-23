*** Settings ***
Documentation    Runs validate.sh with config.json
Suite Setup    Config
Library    OperatingSystem
Library    String


*** Variables ***
${dir}    /stack-validation


*** Keywords ***

Config
    ${output-json} =    Run    cd ${dir} && ./validate.sh | jq -r '.stackValidation.testCases[]'
    Set Suite Variable    ${output-json}
    #Log To Console    ${output-json}

Parse
    [Arguments]    ${tc}
    IF    "${tc}" == "validateKubernetesAPIs" or "${tc}" == "validateSecurityGroups"
        ${pass} =    Run    echo '${output-json}' | jq -r 'select ( .name == "${tc}" ) | .pass'
    END
    IF    "${tc}" == "validateVcpuQuantity" or "${tc}" == "validateSMT" or "${tc}" == "validatePhysicalStorage" or "${tc}" == "validateStorageQuantity" or "${tc}" == "validateVcpuQuantity" or "${tc}" == "validateNFD" or "${tc}" == "validateSystemResourceReservation" or "${tc}" == "validateCPUPinning" or "${tc}" == "validateLinuxDistribution" or "${tc}" == "validateLinuxKernelVersion" or "${tc}" == "validateAnuketProfileLabels"
        ${pass} =    Run    echo '${output-json}' | jq -r 'select ( .name == "${tc}" ) | .nodes[].pass' | sort -u
    END
    IF    "${tc}" == "validateHugepages"
        ${pass} =    Run    echo '${output-json}' | jq -r 'select ( .name == "${tc}" ) | .nodes[].types[].pass' | awk ' $1=="true" { f=1; } END { if (f==1) print "true"; else print "false"; } '
    END
    Set Suite Variable    ${pass}


*** Test Cases ***

#testCaseName
    #[Tags]    testCaseName
    #Should Not Contain    ${output-json}    error:
    #Parse    testCaseName
    #Should Be Equal    ${pass}    true

validateHugepages
    [Tags]    validateHugepages
    Should Not Contain    ${output-json}    error:
    Parse    validateHugepages
    Should Be Equal    ${pass}    true

validateSMT
    [Tags]    validateSMT
    Should Not Contain    ${output-json}    error:
    Parse    validateSMT
    Should Be Equal    ${pass}    true

validatePhysicalStorage
    [Tags]    validatePhysicalStorage
    Should Not Contain    ${output-json}    error:
    Parse    validatePhysicalStorage
    Should Be Equal    ${pass}    true

validateStorageQuantity
    [Tags]    validateStorageQuantity
    Should Not Contain    ${output-json}    error:
    Parse    validateStorageQuantity
    Should Be Equal    ${pass}    true

validateVcpuQuantity
    [Tags]    validateVcpuQuantity
    Should Not Contain    ${output-json}    error:
    Parse    validateVcpuQuantity
    Should Be Equal    ${pass}    true

validateNFD
    [Tags]    validateNFD
    Should Not Contain    ${output-json}    error:
    Parse    validateNFD
    Should Be Equal    ${pass}    true

validateSystemResourceReservation
    [Tags]    validateSystemResourceReservation
    Should Not Contain    ${output-json}    error:
    Parse    validateSystemResourceReservation
    Should Be Equal    ${pass}    true

validateCPUPinning
    [Tags]    validateCPUPinning
    Should Not Contain    ${output-json}    error:
    Parse    validateCPUPinning
    Should Be Equal    ${pass}    true

validateLinuxDistribution
    [Tags]    validateLinuxDistribution
    Should Not Contain    ${output-json}    error:
    Parse    validateLinuxDistribution
    Should Be Equal    ${pass}    true

validateKubernetesAPIs
    [Tags]    validateKubernetesAPIs
    Should Not Contain    ${output-json}    error:
    Parse    validateKubernetesAPIs
    Should Be Equal    ${pass}    true

validateLinuxKernelVersion
    [Tags]    validateLinuxKernelVersion
    Should Not Contain    ${output-json}    error:
    Parse    validateLinuxKernelVersion
    Should Be Equal    ${pass}    true

validateAnuketProfileLabels
    [Tags]    validateAnuketProfileLabels
    Should Not Contain    ${output-json}    error:
    Parse    validateAnuketProfileLabels
    Should Be Equal    ${pass}    true

validateSecurityGroups
    [Tags]    validateSecurityGroups
    Should Not Contain    ${output-json}    error:
    Parse    validateSecurityGroups
    Should Be Equal    ${pass}    true

