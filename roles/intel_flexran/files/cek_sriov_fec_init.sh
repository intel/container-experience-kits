#!/bin/bash
#
# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

DEVBIND_TOOL=${DEVBIND_TOOL:-"/usr/local/bin/dpdk-devbind.py"}
IGB_UIO_PATH=${IGB_UIO_PATH:-"/opt/cek/dpdk-kmods/linux/igb_uio/igb_uio.ko"}
### 0000:f7:00.0 acc200 igb_uio 0
### 0000:f7:00.0 acc200 vfio-pci 1
CEK_FEC_INFO=${FEC_PF_DRIVER:-"/etc/cek/cek_fec_info"}

PFBBCONFIG_DIR=${PFBBCONFIG_DIR:-"/opt/cek/intel-flexran/source/pf-bb-config"}
PFBBCONFIG_TOOL=${PFBBCONFIG_TOOL:-"${PFBBCONFIG_DIR}/pf_bb_config"}
CFG_ACC100_HOST=${CFG_ACC100_HOST:-"${PFBBCONFIG_DIR}/acc100/acc100_config_pf_4g5g.cfg"}
CFG_ACC100_POD=${CFG_ACC100_POD:-"${PFBBCONFIG_DIR}/acc100/acc100_config_vf_5g.cfg"}
CFG_ACC200_HOST=${CFG_ACC200_HOST:-"${PFBBCONFIG_DIR}/acc200/acc200_config_pf_5g.cfg"}
CFG_ACC200_POD=${CFG_ACC200_POD:-"${PFBBCONFIG_DIR}/acc200/acc200_config_vf_5g.cfg"}

configure_fec() {
    if [[ ! -r "${CEK_FEC_INFO}" ]]; then
        echo "File ${CEK_FEC_INFO} doesn't exist."
        return 0
    fi

    while read -r pci_address fec_type pf_driver vf_num; do
        if [[ ${pci_address} == "" ]] || [[ ${fec_type} == "" ]] || [[ ${pf_driver} == "" ]] || [[ ${vf_num} == "" ]]; then
            echo "Empty PCI address or FEC type or pf driver or vf num, skipping..."
            continue
        fi

        if [[ ${pf_driver} == "igb_uio" ]]; then
            numvfs_path="/sys/bus/pci/devices/${pci_address}/max_vfs"
        else
            numvfs_path="/sys/bus/pci/devices/${pci_address}/sriov_numvfs"
        fi

        # reset FEC device
        echo "Cleaning configuration on ${pci_address}"
        # In case of VFIO mode, pf_bb_config runs daemon mode, to reconfigure first kill the existing pf_bb_config process
        if [[ ${pf_driver} == "vfio-pci" ]]; then
            pkill pf_bb_config
        fi

        if [[ -e "${numvfs_path}" ]]; then
            echo 0 > "${numvfs_path}"
        fi
        $DEVBIND_TOOL -u "${pci_address}"

        # Load PF driver
        if [[ -d "/sys/bus/pci/drivers/${pf_driver}" ]]; then
            echo "PF driver: ${pf_driver} already exists, do nothing."
        else
            echo "Bind PF driver: ${pf_driver}"
            if [[ ${pf_driver} == "igb_uio" ]]; then
                if [[ ! -e "${IGB_UIO_PATH}" ]]; then
                    echo " ${IGB_UIO_PATH} doesn't exist."
                    return 0
                fi
                modprobe uio
                insmod "${IGB_UIO_PATH}"
            else
                modprobe "${pf_driver}"
            fi
        fi

        # Bind PF to driver
        $DEVBIND_TOOL -b "${pf_driver}" "${pci_address}"

        # Create VF if needed
        if [[ ${vf_num} -ne 0 ]]; then
            echo 0 > "${numvfs_path}"
            echo "${vf_num}" > "${numvfs_path}"

            # Bind VF to driver
            vf_pci_addrs="$(lspci | grep -i acc | grep -i -e 0d5d -e 57c1 | cut -f1 -d' ')"
            for vf_pci_addr in ${vf_pci_addrs}
            do
                $DEVBIND_TOOL -b vfio-pci "${vf_pci_addr}"
            done
        fi

        # pfBBConfig
        cd "${PFBBCONFIG_DIR}" || exit
        if [[ ${fec_type} == "acc100" ]]; then
            if [[ ${vf_num} -eq 0 ]]; then
                ${PFBBCONFIG_TOOL} "${fec_type}" -c "${CFG_ACC100_HOST}"
            else
                ${PFBBCONFIG_TOOL} "${fec_type}" -c "${CFG_ACC100_POD}"
            fi
        else
            if [[ ${vf_num} -eq 0 ]]; then
                ${PFBBCONFIG_TOOL} "${fec_type}" -c "${CFG_ACC200_HOST}"
            else
                ${PFBBCONFIG_TOOL} "${fec_type}" -v 00112233-4455-6677-8899-aabbccddeeff -c "${CFG_ACC200_POD}"
            fi
        fi
    done < "${CEK_FEC_INFO}"
}

configure_fec
