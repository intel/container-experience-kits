#!/bin/bash

# Copyright (C) 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# options to improve
#   make to work with more than one SRIOV device name

# checkDependencies <command1> [command2]...
function checkDependencies {
    if ! command -v "$1" 1>> /dev/null 2>> /dev/null; then
        echo "ERROR: Install command $1"
        exit 1
    fi
}
checkDependencies kubectl
checkDependencies jq

USAGE="[--debug]"
function usage {
    echo "ERROR. Usage: $0 ${USAGE}"
    exit 2
}

CONFIGFILE=config.json

j=$( cat "${CONFIGFILE}" )
DEBUG=$( echo "${j}" | jq -r ".script.debug" )
case "$#" in
    "0")
        ;;
    "1")
        if [[ "$1" == "--debug" ]]; then
            DEBUG="true"
        else
            usage
        fi
        ;;
    *)
        usage
        ;;
esac

# check k8s permissions
#   add more permissions for all what is used below
function checkPermissions {
    if [[ "$( kubectl auth can-i get nodes -A | grep -c yes || true )" \
        -ne 1 ]]; then
        echo "ERROR: \"Cannot kubectl get nodes. Check permissions.\""
        exit 3
    fi
}

# printBegin <testCaseName>
function printBegin {
    name="$1"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    showDescription=$( echo "${j}" | jq -r ".script.show.description" )
    description=$( echo "${jc}" | jq -r ".description" )
    echo "      \"name\": \"${name}\"",
    if [[ "${showDescription}" == "true" ]]; then
        echo "      \"description\": \"${description}\","
    fi
}

function podCheckSRIOV {
    name="podCheckSRIOV"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    configMapNS=$( echo "${jc}" | jq -r ".configMapNS" )
    configMapName=$( echo "${jc}" | jq -r ".configMapName" )
    configMapSearch=$( echo "${jc}" | jq -r ".configMapSearch" )
    sriovName=$( echo "${jc}" | jq -r ".sriovName" )
    podYAML=$( echo "${jc}" | jq -r ".podYAML" )
    namespace=$( echo "${jc}" | jq -r ".namespace" )
    podName=$( echo "${jc}" | jq -r ".podName" )
    podCountSRIOV=$( echo "${jc}" | jq -r ".podCountSRIOV" )
    podDeployCmd=$( echo "${jc}" | jq -r ".podDeployCmd" )
    podDeleteCmd=$( echo "${jc}" | jq -r ".podDeleteCmd" )
    checkPodEnvVarPCIDev=$( echo "${jc}" | jq -r ".checkPodEnvVarPCIDev" )

    # find name SR-IOV VF devices
    cont="true"
    if [[ "${sriovName}" == "null" ]]; then
        cmName=$( kubectl get ConfigMap -n "${configMapNS}" | grep \
            "${configMapName}" | awk -F' ' '{print $1}' )
        cm=$( kubectl get ConfigMap -n "${configMapNS}" "${cmName}" \
            -o json 2>&1 )
        if [[ "$( echo "${cm}" | grep -c "Error from server (NotFound)" \
            || true )" -eq 1 ]]; then
            cont="false"
            m="error: NotFound ${configMapName}"
        else
            s=$( echo "${cm}" | jq -r " .data.\"config.json\"" | \
                jq -r ".resourceList[] | select ( .resourceName | \
                contains(\"${configMapSearch}\") ) " || true )
            sn=$( echo "${s}" | jq -r " .resourceName " )
            v=$( echo "${s}" | jq -r " .selectors.vendors[] " )
            pciids=$( wget --timeout=20 -qO - \
                https://pciids.sourceforge.net/v2.2/pci.ids )
            vn=$( echo "${pciids}" | sed "/^#/d; /^\t/d;" | \
                    awk -vvid="${v}" \
                    ' $1==vid { printf("%s.com",tolower($2)) } ' )
            if [ "${vn}" == "" ]; then
                vn="unknown"
            fi
            sriovName="${vn}/${sn}"
        fi
    fi
    #echo "sriovName=${sriovName}"

    echo -n "      \"pass\": "
    if [[ "${cont}" == "false" ]]; then
        echo -n "false"
    else
        envVar="PCIDEVICE_$( echo "${sriovName}" | tr '[:lower:]' '[:upper:]' \
            | tr './' '_' || true )"
        m="sriovName=${sriovName};"

        # find pod name in pod YAML (if not set in config.json)
        py=$( tr -d "'\"" < "${podYAML}" )
        if [[ "${namespace}" == "null" ]]; then
            namespace=$( echo "${py}" | awk " \$1==\"metadata:\" { f=1; } \
                f==1 && \$1==\"namespace:\" { print \$2 } " )
        fi
        if [[ "${podName}" == "null" ]]; then
            podName=$( echo "${py}" | awk " \$1==\"metadata:\" { f=1; } \
                f==1 && \$1==\"name:\" { print \$2 } " )
        fi

        # find how many VFs are in pod YAML
        #   note that this might not be correct number for some k8s assets like
        #     daemonset so then set podCountSRIOV in config.json
        if [[ "${podCountSRIOV}" == "null" ]]; then
            podCountSRIOV=$( echo "${py}" | awk -vsn="${sriovName}" \
                " \$1==\"spec:\" { f1=1; } \
                f1==1 && \$1==\"containers:\" { f2=1; } \
                f2==1 && \$1==\"resources:\" { f3=1; } \
                f3==1 && \$1==\"limits:\" { f4=1; } \
                f4==1 && \$1==sn\":\" { s+=\$2; f4=0; } \
                END { print s } " )
        fi
        #echo "podCountSRIOV=${podCountSRIOV}"
        m="${m} podCountSRIOV=${podCountSRIOV};"

        # before find VFs per worker node
        nc=0
        for n in ${NODES}; do
            nodeName[nc]="${n}"
            nodeBeforeCountSRIOV[nc]=$( kubectl describe no "${n}" | \
                awk " BEGIN { p=0 } \
                    \$1==\"Resource\" && \$2==\"Requests\" { p=1 } \
                    \$1==\"Events:\" { p=0 } \
                    { if (p) { p++; print \$0; } } " | \
                    grep "${sriovName}" | awk ' { print $2 } ' || true )
            nc=$((nc+1))
        done
        nbc=0
        for i in 0 $( seq "$( echo "${nc}" - 1 | bc || true )"); do
            #nbc=$((nbc + nodeBeforeCountSRIOV[${i}]))
            nbc=$((nbc + nodeBeforeCountSRIOV[i]))
            #echo "nodeBeforeCountSRIOV[${i}]=${nodeBeforeCountSRIOV[${i}]}"
        done
        #echo "nbc=${nbc}"

        # deploy CNF
        ${podDeployCmd} 1>>/dev/null 2>>/dev/null

        # wait till CNF comes up
        sleep "${podPause}"

        # after find VFs per worker node
        nc=0
        for n in ${NODES}; do
            nodeAfterCountSRIOV[nc]=$( kubectl describe no "${n}" | \
                awk " BEGIN { p=0 } \
                    \$1==\"Resource\" && \$2==\"Requests\" { p=1 } \
                    \$1==\"Events:\" { p=0 } \
                    { if (p) { p++; print \$0; } } " | \
                    grep "${sriovName}" | awk ' { print $2 } ' || true )
            nc=$((nc+1))
        done
        nac=0
        for i in 0 $( seq "$( echo "${nc}" - 1 | bc || true )"); do
            #nac=$((nac + nodeAfterCountSRIOV[${i}]))
            nac=$((nac + nodeAfterCountSRIOV[i]))
            #echo "nodeAfterCountSRIOV[${i}]=${nodeAfterCountSRIOV[${i}]}"
            if [[ "${nodeBeforeCountSRIOV[${i}]}" -ne \
                "${nodeAfterCountSRIOV[${i}]}" ]]; then
                m="${m} nodeName=${nodeName[${i}]},"
                m="${m} beforeCountSRIOV=${nodeBeforeCountSRIOV[${i}]},"
                m="${m} afterCountSRIOV=${nodeAfterCountSRIOV[${i}]};"
            fi
        done
        #echo "nac=${nac}"

        if [[ "${nac}" -eq "${nbc}" ]]; then
            echo -n "false"
            m="${m} beforeClusterCountSRIOV=${nbc},"
            m="${m} afterClusterCountSRIOV=${nac};"
            pm=$( kubectl get po -n "${namespace}" "${podName}" -o json | \
                jq -r ".status.conditions[].message" | grep -v null | sort -u \
                || true )
            m="${m} podMessage=${pm};"
        else
            if [[ "${checkPodEnvVarPCIDev}" == "false" ]]; then
                echo -n "true"
            else # check env vars in pod's containers
                #echo podName=$podName
                #echo envVar=$envVar
                envVarCount=0
                containerNames=$( kubectl get po -n "${namespace}" \
                    "${podName}" -o json | jq -r \
                    ".status.containerStatuses[].name" 2>&1 || true )
                if [[ "$( echo "${containerNames}" | grep -c \
                    "Cannot iterate over null" || true )" -eq 1 ]]; then
                    echo -n "false"
                else
                    for c in ${containerNames}; do
                        #echo "c=${c}"
                        ev=$( kubectl exec -it -n "${namespace}" "${podName}" \
                            -c "${c}" -- env | awk -vFS="=" -vEV="${envVar}" \
                            ' $1==EV { print $2 } ' | strings || true )
                        #echo ">>> ev=${ev} <<<"
                        fe=$( echo "${ev}" | tr "," " " | wc -w || true )
                        #echo "fe=${fe}"
                        envVarCount=$((envVarCount + fe))
                        if [[ "${ev}" != "" ]]; then
                            m="${m} containerName=${c}, ${envVar}=${ev};"
                        fi
                    done
                    # print result
                    #echo -n "nbc=${nbc}, nac=${nac}, "
                    #echo "podCountSRIOV=${podCountSRIOV}"
                    if [[ "${nac}" -eq "$((nbc + podCountSRIOV))" ]]; then
                        if [[ "${checkPodEnvVarPCIDev}" == "true" ]]; then
                            if [[ "${envVarCount}" -eq "${podCountSRIOV}" ]]; \
                                then
                                echo -n "true"
                            else
                                echo -n "false"
                            fi
                        else
                            echo -n "true"
                        fi
                    else
                        echo -n "false"
                    fi
                fi
            fi
        fi
    fi
    if [[ "${DEBUG}" == "true" ]]; then
        echo ","
        echo "      \"debug\": \"${m}\""
    fi

    # delete CNF
    ${podDeleteCmd} 1>>/dev/null 2>>/dev/null &
}


# main

checkPermissions
NODES=$( kubectl get no -o json | jq -r ".items[].metadata.name" || true )
podPause=$( echo "${j}" | jq -r ".script.podPause" )

echo "{"
echo "  \"CNFValidation\": ["
startTime=$( date )

echo "    {"
podCheckSRIOV
echo "    }"

echo -n "  ]"

showTimeStamps=$( echo "${j}" | jq -r ".script.show.timeStamps" )
if [[ "${showTimeStamps}" == "true" ]]; then
    echo ","
    echo "  \"timeStamps\": {"
    echo "    \"start\": \"${startTime}\","
    stopTime=$( date )
    echo "    \"stop\": \"${stopTime}\""
    echo "  }"
else
    echo
fi

echo "}"
