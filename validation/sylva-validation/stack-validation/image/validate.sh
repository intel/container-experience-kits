#!/bin/bash

# Copyright (C) 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# To Do:
#   split into multiple scripts?
#   cache list of pods?
#   parallelize kubectl exec across multiple pods?

# checkDependencies <command1> [command2]...
function checkDependencies {
    if ! command -v "$1" 1>> /dev/null 2>> /dev/null; then
        echo "ERROR: Install command $1"
        exit 1
    fi
}
checkDependencies kubectl
checkDependencies jq

USAGE="[--only <testname>] [--debug]"
function usage {
    echo "ERROR. Usage: $0 ${USAGE}"
    exit 2
}

CONFIGFILE=config.json

j=$( cat "${CONFIGFILE}" )
ro=""
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
    "2")
        if [[ "$1" == "--only" ]]; then
            ro="$2"
        else
            usage
        fi
        ;;
    "3")
        if [[ "$1" == "--only" ]]; then
            ro="$2"
            if [[ "$3" == "--debug" ]]; then
                DEBUG="true"
            else
                usage
            fi
        elif [[ "$1" == "--debug" ]]; then
            DEBUG="true"
            if [[ "$2" == "--only" ]]; then
                ro="$3"
            else
                usage
            fi
        else
            usage
        fi
        ;;
    *)
        usage
        ;;
esac

PODPAUSE=$( echo "${j}" | jq -r ".script.podPause" )
DIRECTORY=$( echo "${j}" | jq -r ".script.deployFiles.directory" )
NS=$( echo "${j}" | jq -r ".script.podNamespace" )
HUGE=$( echo "${j}" | jq -r ".script.deployFiles.huge.name" )
MULTI=$( echo "${j}" | jq -r ".script.deployFiles.multi.name" )
RESERVE=$( echo "${j}" | jq -r ".script.deployFiles.reserve.name" )
NETPOLICY=$( echo "${j}" | jq -r ".script.deployFiles.netPolicy" )
NETPOLICYPAUSE=$( echo "${j}" | jq -r ".script.netPolicyPause" )

# check k8s permissions
#   add more permissions for all what is used below
function checkPermissions {
    if [[ "$( kubectl auth can-i get nodes -A | grep -c yes || true )" \
        -ne 1 ]]; then
        echo "ERROR: \"Cannot kubectl get nodes. Check permissions.\""
        exit 3
    fi
}

function createNamespace {
    if [[ "$( kubectl get ns | grep -c "${NS}" || true )" -ne 1 ]]; then
        kubectl create ns "${NS}" >> /dev/null
    fi
}

function deleteNamespace {
    kubectl delete ns "${NS}" >> /dev/null
}

function checkEmptyNamespace {
    if [[ "$( kubectl get po -n "${NS}" -o json | jq -r ".items[]" |\
        wc -l || true )" -gt 0 ]]; then
        echo -n "        \"error\": \"There are already pods running in "
        echo "namespace ${NS}.\""
        echo "  }"
        echo "}"
        exit 4
    fi
}

# createDaemonset <shortname> [--with-sleep]
function createDaemonset {
    kubectl apply -f "${DIRECTORY}/$1.yaml" >> /dev/null
    if [[ "$2" == "--with-sleep" ]]; then
        sleep "${PODPAUSE}"
    fi
}

# createDaemonsetHuge [--with-sleep]
function createDaemonsetHuge {
    name="validateHugepages"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " \
        || true )
    hptypes=$( echo "${jc}" | jq -r ".types[].name " || true )
    for hp in ${hptypes}; do
        createDaemonset "${HUGE}${hp,,}"  # ,, gets it to lowercase
    done
    if [[ "$1" == "--with-sleep" ]]; then
        sleep "${PODPAUSE}"
    fi
}

# deleteDaemonset <shortname>
function deleteDaemonset {
    kubectl delete -f "${DIRECTORY}/$1.yaml" >> /dev/null &
}

function deleteDaemonsetHuge {
        name="validateHugepages"
        jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) \
            " || true )
        hptypes=$( echo "${jc}" | jq -r ".types[].name " || true )
        for hp in ${hptypes}; do
                deleteDaemonset "${HUGE}${hp,,}"
        done
}

# printBegin <testCaseName>
function printBegin {
    name="$1"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " \
        || true )
    showDescription=$( echo "${j}" | jq -r ".script.show.description" || true )
    description=$( echo "${jc}" | jq -r ".description" || true )
    showRa2Spec=$( echo "${j}" | jq -r ".script.show.ra2Spec" || true )
    ra2Spec=$( echo "${jc}" | jq -r ".ra2Spec" || true )
    echo "      {"
    echo "        \"name\": \"${name}\"",
    if [[ "${showDescription}" == "true" ]]; then
        echo "        \"description\": \"${description}\","
    fi
    if [[ "${showRa2Spec}" == "true" ]]; then
        echo "        \"ra2Spec\": \"${ra2Spec}\","
    fi
}

# rework to check for rpm/deb and not osImage?
function validateLinuxDistribution {
    name="validateLinuxDistribution"
    printBegin "${name}"
    echo "        \"nodes\": ["
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " \
        || true )
    g=$( echo "${jc}" | jq -r " .distroNames[].name " | awk " { a[NR]=\$0 } \
        END {for (i=1;i<NR;i++) printf(\"%s|\",a[i]); print a[NR]; } " || true )
    e1=1 # 1st element
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        o=$( kubectl get no "${n}" -o json | jq -r ".status.nodeInfo.osImage" \
            || true )
        if [[ "$( echo "${o}" | grep -c -E "${g}" || true )" -eq 1 ]]; then
            echo -n "            \"pass\": true"
        else
            echo -n "            \"pass\": false"
        fi
        if [[ "${DEBUG}" == "true" ]]; then
            echo ","
            echo "            \"debug\": \"osImage=${o}\""
        else
            echo
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

function validateKubernetesAPIs {
    name="validateKubernetesAPIs"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    exceptions=$( echo "${jc}" | jq -r ".exceptions[].name" )
    #g=$( echo "${exceptions}" | sed "s/ /|/g" )
    g="${exceptions// /|}"
    alphaAPIs=$( kubectl api-resources --cached=false | \
        awk ' $2~"alpha" { print $2 } $3~"alpha" { print $3 } ' | sort -u \
        || true )
    betaAPIs=$( kubectl api-resources --cached=false | \
        awk ' $2~"beta" { print $2 } $3~"beta" { print $3 } ' | sort -u \
        || true )
    r=1
    for a in ${alphaAPIs}; do
        if [[ "$( echo "${a}" | grep -cE "${g}" || true )" -ne 1 ]]; then
            r=0
        fi
    done
    #minor=$( kubectl version -o json | jq -r ".serverVersion.minor" | \
    #    tr -d -c 0-9 )
    #if [ "${minor}" -ge "24" ]; then  # no beta after 1.24
    #    if [ "$betaAPIs" != "" ]; then
    #        r=0
    #    fi
    #else
        for b in ${betaAPIs}; do
            if [[ "$( echo "${b}" | grep -cE "${g}" || true )" -ne 1 ]]; then
                r=0
            fi
        done
    #fi
    if [[ "${r}" -eq "1" ]]; then
        echo -n "        \"pass\": true"
    else
        echo -n "        \"pass\": false"
    fi
    if [[ "${DEBUG}" == "true" ]]; then
        echo ","
        echo -n "        \"debug\": \"alphaAPIs="
        echo "${alphaAPIs}" | awk " { a[NR]=\$0 } END { for (i=1;i<NR;i++) \
            printf(\"%s \",a[i]); printf(\"%s\",a[i]); } "
        echo -n "  betaAPIs="
        echo "${betaAPIs}" | awk " { a[NR]=\$0 } END { for (i=1;i<NR;i++) \
            printf(\"%s \",a[i]); printf(\"%s\",a[i]); } "
        echo "\""
    else
        echo
    fi
    echo -n "      }"
}

function validateLinuxKernelVersion {
    name="validateLinuxKernelVersion"
    printBegin "${name}"
    echo "        \"nodes\": ["
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    minMajor=$( echo "${jc}" | jq -r ".minMajor" )
    minMinor=$( echo "${jc}" | jq -r ".minMinor" )
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        kernelVersion=$( kubectl get no "${n}" -o json | \
            jq -r ".status.nodeInfo.kernelVersion" || true )
        major=$( echo "${kernelVersion}" | awk -vFS="." ' { print $1 } ' )
        minor=$( echo "${kernelVersion}" | awk -vFS="." ' { print $2 } ' )
        echo -n "            \"pass\": "
        if [[ "${major}" -gt "${minMajor}" ]]; then
            echo -n "true"
        else
            if [[ "${major}" -eq "${minMajor}" ]]; then
                if [[ "${minor}" -lt "${minMinor}" ]]; then
                    echo "false"
                else
                    echo "true"
                fi
            else
                echo "false"
            fi
        fi
        if [[ "${DEBUG}" == "true" ]]; then
            echo ","
            echo "            \"debug\": \"kernelVersion=${kernelVersion}\""
        else
            echo
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

function validateAnuketProfileLabels {
    name="validateAnuketProfileLabels"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    labelKey=$( echo "${jc}" | jq -r ".anuketProfileLabelKey" )
    labelValues=$( echo "${jc}" | jq -r ".anuketProfileLabelValues[].name" )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        for alk in ${labelKey}; do
            lv=$( kubectl get no "${n}" -o json | \
                jq -r ".metadata.labels.\"${alk}\"" || true )
            pass="false"
            value="undefined"
            for v in ${labelValues}; do
                if [[ "$( echo "${lv}" | grep -c -e "${v}" || true )" \
                    -eq 1 ]]; then
                    pass="true"
                    value="${lv}"
                fi
            done
            echo -n "            \"pass\": ${pass}"
            if [[ "${DEBUG}" == "true" ]]; then
                echo ","
                echo -n "            \"debug\": "
                if [[ "${pass}" == "true" ]]; then
                    echo "\"${alk}=${value}\""
                else
                    if [[ "${value}" == "undefined" ]]; then
                        echo "\"${alk} not set\""
                    else
                        echo "\"${alk}=${value}\""
                    fi
                fi
            else
                echo
            fi
        done
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

# validate huge pages, normally 1Gi and 2Mi
function validateHugepages {
    name="validateHugepages"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    hptypes=$( echo "${jc}" | jq -r ".types[].name " )
    echo "        \"nodes\": ["
    e1=1; # 1st element
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        echo "            \"types\": ["
        e2=1 # 1st element
        for hp in ${hptypes}; do
            if [[ "${e2}" -eq 1 ]]; then
                e2=0
            else
                echo ","
            fi
            echo "              {"
            echo "                \"name\": \"${hp}\","
            v=$( kubectl get no "${n}" -o json | \
                jq -r ".status.allocatable.\"hugepages-${hp}\"" | \
                sed -e "s/Mi//g" -e "s/Gi//g" || true )
            r="true"
            if [[ ! "${v}" -gt "0" ]]; then
                r="false"
            fi
            p=$( kubectl get po -n "${NS}" -o json | jq -r " .items[] | \
                select( .metadata.generateName==\"test-${HUGE}${hp,,}-\" \
                and .spec.nodeName==\"${n}\" ) | .metadata.name " || true )
            if [[ "${p}" == "" ]]; then
                r="false"
            else
                log=$( kubectl logs -n "${NS}" "${p}" )
                if [[ "$( echo "${log}" | tail -1 || true )" -ne 1 ]]; then
                    r="false"
                fi
                l=$( echo "${log}" | awk " { a[NR]=\$0 } END \
                    { for (i=1;i<NR-1;i++) printf(\"%s \",a[i]); \
                    printf(\"%s\",a[i]); } " )
            fi
            echo -n "                \"pass\": ${r}"
            if [[ "${DEBUG}" == "true" ]]; then
                echo ","
                if [[ "${p}" == "" ]]; then
                    m=$( kubectl get po -n "${NS}" -o json | jq -r ".items[] \
| select( .metadata.generateName==\"test-${HUGE}${hp,,}-\" and \
.spec.affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution.\
nodeSelectorTerms[].matchFields[].values[]==\"${n}\" ) | \
.status.conditions[].message" || true )
                    echo -n "                \"debug\": \"Cluster reported: "
                    echo "hugepages-${hp}=${v}.  Pod describe message: ${m}\""
                fi
                if [[ "${r}" == "true" ]]; then
                    echo -n "                \"debug\": \"Cluster reported: "
                    echo "hugepages-${hp}=${v}.  Pod reported: ${l}\""
                fi
            else
                echo
            fi
            echo -n "              }"
        done
        echo
        echo "            ]"
        echo "          }"
    done
    echo "        ]"
    echo -n "      }"
}

# validate SMT by checking /proc/cpuinfo
#   assumes either no hypervisor or that hypervisor is not emulating SMT
function validateSMT {
    name="validateSMT"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        echo -n "            \"pass\": "
        p=$( kubectl get po -n "${NS}" -o json | \
            jq -r ".items[] | select( \
                .metadata.generateName==\"test-${MULTI}-\" and \
                .spec.nodeName==\"${n}\" ) | .metadata.name" || true )
        if [[ "${p}" == "" ]]; then
            echo "false,"
            echo "            \"error\": \"Didn't find running test pod.\""
        else
            phcpus=$( kubectl exec -t -n "${NS}" "${p}" -- cat /proc/cpuinfo \
                | grep "^physical id" /proc/cpuinfo | sort -u | wc -l || true )
            phcores=$( kubectl exec -t -n "${NS}" "${p}" -- cat /proc/cpuinfo \
                | grep "^core id" | sort -u | wc -l || true )  # per phcpu
            vcpus=$( kubectl exec -t -n "${NS}" "${p}" -- cat /proc/cpuinfo | \
                grep -c "^processor" || true )
            if [[ "$(( phcores * phcpus * 2 ))" -eq "${vcpus}" ]]; then
                echo -n "true"
            else
                echo -n "false"
            fi
            if [[ "${DEBUG}" == "true" ]]; then
                echo ","
                echo -n "            \"debug\": \"phcpus=${phcpus}, "
                echo "phcores=${phcores}, vcpus=${vcpus}\""
            else
                echo
            fi
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

# validate phyisical storage with SSD
#   can be improved by looking for pci.ids deviceIDs
function validatePhysicalStorage {
    name="validatePhysicalStorage"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    limit=$( echo "${jc}" | jq -r ".limit" )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        echo -n "            \"pass\": "
        p=$( kubectl get po -n "${NS}" -o json | jq -r ".items[] | \
            select( .metadata.generateName==\"test-${MULTI}-\" \
            and .spec.nodeName==\"${n}\" ) | .metadata.name" || true )
        if [[ "${p}" == "" ]]; then
            echo "false,"
            echo "            \"error\": \"Didn't find running test pod.\""
        else
            l="$( kubectl logs -n "${NS}" "${p}" )"
            if [[ "$( echo "${l}" | grep -c "SSD" || true )" -ge 1 ]]; then
                echo -n "true"
            else
                echo -n "false"
            fi
            if [[ "${DEBUG}" == "true" ]]; then
                echo ","
                echo -n "            \"debug\": \""
                w="$( echo "${l}" | grep "^wget" )"
                if [[ "${w}" != "" ]]; then
                    echo -n "${w}" | sed "s/://g"
                    echo -n "; "
                fi
                echo -n "pcidev="
                pcidev=$( kubectl logs -n "${NS}" "${p}" | \
                    grep "^pcidev=" | sort -u | \
                    awk ' { $1=""; printf("%s, ",$0); } ' | sed "s/  / /g" | \
                    sed "s/ (unknown)//g" | xargs || true )
                echo "${pcidev%?}\""  # %? deletes last ","
            else
                echo
            fi
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

function validateStorageQuantity {
    name="validateStorageQuantity"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    limit=$( echo "${jc}" | jq -r ".limit" )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        # gets storage quantity in Gi bytes
        g=$( kubectl get no "${n}" -o json | jq -r \
            ".status.allocatable.\"ephemeral-storage\"" | \
            awk " { r=\$1; if (\$1~/Ki/){r*=1024}; if (\$1~/Mi/){r*=1024**2}; \
                if (\$1~/Gi/){r*=1024**3}; if (\$1~/Ti/){r*=1024**4}; \
                print int(r/2^30); } " || true )
        if [[ "${g}" -lt "${limit}" ]]; then
            echo -n "            \"pass\": false"
        else
            echo -n "            \"pass\": true"
        fi
        if [[ "${DEBUG}" == "true" ]]; then
            echo ","
            echo "            \"debug\": \"ephemeral_storage=${g}GiB\""
        else
            echo
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

function validateVcpuQuantity {
    name="validateVcpuQuantity"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    limit=$( echo "${jc}" | jq -r ".limit" )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        c=$( kubectl get no "${n}" -o json | jq -r ".status.capacity.cpu" \
            || true )
        if [[ "${c}" -gt "${limit}" ]]; then
            echo -n "            \"pass\": true"
        else
            echo -n "            \"pass\": false"
        fi
        if [[ "${DEBUG}" == "true" ]]; then
            echo ","
            echo "            \"debug\": \"vcpu=${c}\""
        else
            echo
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

# validate CPU Manager by checking cgroups cpusets and node label
function validateCPUPinning {
    name="validateCPUPinning"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        echo -n "            \"pass\": "
        p=$( kubectl get po -n "${NS}" -o json | jq -r ".items[] | \
            select( .metadata.generateName==\"test-${MULTI}-\" \
            and .spec.nodeName==\"${n}\" ) | .metadata.name" || true )
        if [[ "${p}" == "" ]]; then
            echo "false,"
            echo "            \"error\": \"Didn't find running test pod.\""
        else
            l=$( kubectl logs -n "${NS}" "${p}" )
            if [[ "$( echo "${l}" | awk -vFS="=" " \$1==\"cpusetlimited\" \
                { l=\$2; f=1; } END { if (f) print l; else print 0 } " \
                || true )" -eq 1 ]]; then
                echo -n "true"
            else
                echo -n "false"
            fi
            if [[ "${DEBUG}" == "true" ]]; then
                echo ","
                allrange=$( echo "${l}" | awk -vFS="=" \
                    ' $1=="allrange" { print $2 } ' )
                cpusetcpus=$( echo "${l}" | awk -vFS="=" \
                    ' $1=="cpusetcpus" { print $2 } ' )
                echo -n "            \"debug\": \"allrange=${allrange} "
                echo "cpusetcpus=${cpusetcpus}\""
            else
                echo
            fi
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

# validate NFD by checking for enough NFD labels
function validateNFD {
    name="validateNFD"
    printBegin "${name}"
    jc=$( echo "${j}" | jq ".testCases[] | select ( .name==\"${name}\" ) " )
    nFDLabelPrefix=$( echo "${jc}" | jq -r ".nFDLabelPrefix" )
    limit=$( echo "${jc}" | jq -r ".limit" )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        lc=$( kubectl get node "${n}" -o yaml | grep "${nFDLabelPrefix}" | \
            sort -u | wc -l || true )
        if [[ "${lc}" -gt "${limit}" ]]; then
            echo -n "            \"pass\": true"
        else
            echo -n "            \"pass\": false"
        fi
        if [[ "${DEBUG}" == "true" ]]; then
            echo ","
            echo "            \"debug\": \"${lc} labels\""
        else
            echo
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

function validateSystemResourceReservation {
    name="validateSystemResourceReservation"
    printBegin "${name}"
    jc=$( echo "${j}" | jq " .testCases[] | select ( .name==\"${name}\" ) " \
        || true )
    checks=$( echo "${jc}" | jq -r ".checks[]" || true )
    len=$( echo "${checks}" | jq -r ".process" | wc -l || true )
    echo "        \"nodes\": ["
    e1=1
    for n in ${NODES}; do
        if [[ "${e1}" -eq 1 ]]; then
            e1=0
        else
            echo ","
        fi
        echo "          {"
        echo "            \"name\": \"${n}\","
        r="false"
        m="Command=not found"
        for i in $( seq "${len}" ); do
            pr=$( echo "${checks}" | jq -r ".process" | \
                awk -vl="${i}" ' NR==l { print $1 } ' || true )
            fl=$( echo "${checks}" | jq -r ".flag" | \
                awk -vl="${i}" ' NR==l { print $1 } ' || true )
            p=$( kubectl get po -n "${NS}" -o json | jq -r ".items[] | \
                select( .metadata.generateName==\"test-${RESERVE}-\" \
                and .spec.nodeName==\"${n}\" ) | .metadata.name " || true )
            if [[ "${p}" == "" ]]; then
                echo -n "            \"error\": \"Cannot find "
                echo "validate-${RESERVE} pod on node ${n}\","
            else
                cmd=$( kubectl exec -t -n "${NS}" "${p}" -- \
                    sh -c "ps -ef | grep ${pr} | grep -v grep" 2>> /dev/null \
                    || true )
                g=$( echo "${cmd}" | grep -c "\-\-${fl}" )
                if [[ "${g}" -eq "1" ]]; then
                    r="true"
                    m="Command=${cmd}"
                fi
            fi
        done
        echo -n "            \"pass\": ${r}"
        if [[ "${DEBUG}" == "true" ]]; then
            echo ","
            echo "            \"debug\": \"${m}\""
        else
            echo
        fi
        echo -n "          }"
    done
    echo
    echo "        ]"
    echo -n "      }"
}

# this is test as per
# https://kubernetes.io/docs/tasks/administer-cluster/declare-network-policy/
function validateSecurityGroups {
    name="validateSecurityGroups"
    printBegin "${name}"
    kubectl create deployment -n "${NS}" nginx --image=nginx 1>> /dev/null
    kubectl expose deployment -n "${NS}" nginx --port=80 1>> /dev/null
    sleep "${PODPAUSE}"
    phase=$( kubectl get po -n "${NS}" -o json | jq -r ".items[] | \
        select( .metadata.labels.app==\"nginx\" ) | .status.phase " || true )
    if [[ "${phase}" != "Running" ]]; then
        echo -n "        \"pass\": false"
        if [[ "${DEBUG}" == "true" ]]; then
            echo ","
            echo "        \"debug\": \"Cannot create deployment+pod nginx\""
        else
            echo
        fi
    else
        p=$( kubectl get po -n "${NS}" -o json | jq -r ".items[] | \
            select( .metadata.generateName==\"test-${MULTI}-\" ) | \
            .metadata.name " | head -1 || true )
        if [[ "${p}" == "" ]]; then
            echo "        \"pass\": false,"
            echo "        \"debug\": \"Cannot find running test pod\""
        else
            c=$( kubectl exec -t -n "${NS}" "${p}" -- wget -q -T 1 -O - nginx \
                2>> /dev/null | grep -c "Welcome" || true )
            if [[ "${c}" -eq "0" ]]; then
                echo -n "        \"pass\": false"
                if [[ "${DEBUG}" == "true" ]]; then
                    echo ","
                    echo "    debug: \"Cannot reach nginx\""
                else
                    echo
                fi
            else
                kubectl apply -f "${DIRECTORY}/${NETPOLICY}.yaml" 1>> /dev/null
                sleep "${NETPOLICYPAUSE}"
                c=$( kubectl exec -t -n "${NS}" "${p}" -- wget -q -T 1 -O - \
                    nginx 2>> /dev/null | grep -c "Welcome" || true )
                if [[ "${c}" -gt "0" ]]; then
                    echo -n "        \"pass\": false"
                    if [[ "${DEBUG}" == "true" ]]; then
                        echo ","
                        echo -n "        \"debug\": \"Can reach nginx after "
                        echo "NetworkPolicy applied and before label set\""
                    else
                        echo
                    fi
                else
                    kubectl label po -n "${NS}" "${p}" access=true \
                        1>> /dev/null
                    sleep 1
                    c=$( kubectl exec -t -n "${NS}" "${p}" -- \
                        wget -q -T 1 -O - nginx 2>> /dev/null | \
                        grep -c "Welcome" || true )
                    if [[ "${c}" -eq "0" ]]; then
                        echo -n "        \"pass\": false"
                        if [[ "${DEBUG}" == "true" ]]; then
                            echo ","
                            echo -n "        \"debug\": \"Cannot reach nginx "
                            echo -n "after NetworkPolicy applied and label "
                            echo "set\""
                        else
                            echo
                        fi
                    else
                        echo -n "        \"pass\": true"
                        if [[ "${DEBUG}" == "true" ]]; then
                            echo ","
                            echo -n "        \"debug\": \"All OK: Without "
                            echo -n "NetworkPolicy can reach nginx. With "
                            echo -n "NetworkPolicy without label cannot reach "
                            echo -n "nginx. With NetworkPolicy with label can "
                            echo "reach nginx.\""
                        else
                            echo
                        fi
                    fi
                fi
                kubectl delete -f "${DIRECTORY}/${NETPOLICY}.yaml" \
                    1>> /dev/null &
            fi
        fi
    fi
    kubectl delete svc -n "${NS}" nginx 1>> /dev/null &
    kubectl delete deployment -n "${NS}" nginx 1>> /dev/null &
    echo -n "      }"
}


# main

checkPermissions
NODES=$( kubectl get no -o json | jq -r ".items[].metadata.name" || true )

echo "{"
echo "  \"stackValidation\": {"

startTime=$( date )

tcrun=1
if [[ "${ro}" == "" ]]; then
    createNamespace
    checkEmptyNamespace
    createDaemonsetHuge
    createDaemonset "${MULTI}"
    createDaemonset "${RESERVE}"
    sleep "${PODPAUSE}"
    echo "    \"testCases\": ["
    validateHugepages
    echo ","
    validateSMT
    echo ","
    validatePhysicalStorage
    echo ","
    validateStorageQuantity
    echo ","
    validateVcpuQuantity
    echo ","
    validateNFD
    echo ","
    validateSystemResourceReservation
    echo ","
    validateCPUPinning
    echo ","
    validateLinuxDistribution  # needs more testing
    echo ","
    validateLinuxKernelVersion
    echo ","
    validateKubernetesAPIs
    echo ","
    validateAnuketProfileLabels
    echo ","
    validateSecurityGroups
    echo
    deleteDaemonsetHuge
    deleteDaemonset "${MULTI}"
    deleteDaemonset "${RESERVE}"
    deleteNamespace
else
    case "${ro}" in
        "validateHugepages")
            createNamespace
            checkEmptyNamespace
            createDaemonsetHuge --with-sleep
            echo "    \"testCases\": ["
            validateHugepages
            echo
            deleteDaemonsetHuge
            deleteNamespace
            ;;
        "validateSMT")
            createNamespace
            checkEmptyNamespace
            createDaemonset "${MULTI}" --with-sleep
            echo "    \"testCases\": ["
            validateSMT
            echo
            deleteDaemonset "${MULTI}"
            deleteNamespace
            ;;
        "validatePhysicalStorage")
            createNamespace
            checkEmptyNamespace
            createDaemonset "${MULTI}" --with-sleep
            echo "    \"testCases\": ["
            validatePhysicalStorage
            echo
            deleteDaemonset "${MULTI}"
            deleteNamespace
            ;;
        "validateStorageQuantity")
            echo "    \"testCases\": ["
            validateStorageQuantity
            echo
            ;;
        "validateVcpuQuantity")
            echo "    \"testCases\": ["
            validateVcpuQuantity
            echo
            ;;
        "validateNFD")
            echo "    \"testCases\": ["
            validateNFD
            echo
            ;;
        "validateSystemResourceReservation")
            createNamespace
            checkEmptyNamespace
            createDaemonset "${RESERVE}" --with-sleep
            echo "    \"testCases\": ["
            validateSystemResourceReservation
            echo
            deleteDaemonset "${RESERVE}"
            deleteNamespace
            ;;
        "validateCPUPinning")
            createNamespace
            checkEmptyNamespace
            createDaemonset "${MULTI}" --with-sleep
            echo "    \"testCases\": ["
            validateCPUPinning
            echo
            deleteDaemonset "${MULTI}"
            deleteNamespace
            ;;
        "validateLinuxDistribution")
            echo "    \"testCases\": ["
            validateLinuxDistribution
            echo
            ;;
        "validateKubernetesAPIs")
            echo "    \"testCases\": ["
            validateKubernetesAPIs
            echo
            ;;
        "validateLinuxKernelVersion")
            echo "    \"testCases\": ["
            validateLinuxKernelVersion
            echo
            ;;
        "validateAnuketProfileLabels")
            echo "    \"testCases\": ["
            validateAnuketProfileLabels
            echo
            ;;
        "validateSecurityGroups")
            createNamespace
            checkEmptyNamespace
            createDaemonset "${MULTI}" --with-sleep
            echo "    \"testCases\": ["
            validateSecurityGroups
            echo
            deleteDaemonset "${MULTI}"
            deleteNamespace
            ;;
        *)
            echo "    \"error\": \"Cannot find testcase ${ro}\""
            tcrun=0
            ;;
    esac
fi

if [[ "${tcrun}" -eq 1 ]]; then
    echo "    ]"
fi
echo -n "  }"

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

