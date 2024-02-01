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

SRIOV_NUMVFS_MAPPINGS=${SRIOV_NUMVFS_MAPPINGS:-"/etc/cek/cek_sriov_numvfs"}

setup_vfs_mac() {
    echo "Setting up VFs MAC for FlexRAN"
    if [[ ! -r "${SRIOV_NUMVFS_MAPPINGS}" ]]; then
        echo "File ${SRIOV_NUMVFS_MAPPINGS} doesn't exist, no VFs MAC will be configured"
        return 0
    fi

    j=0
    while read -r pci_address numvfs interface_name; do
        echo "${pci_address}"
        for i in $(seq "${numvfs}")
        do
            ip link set "${interface_name}" vf $((i-1)) mac 00:11:22:33:00:$((i-1))${j}
        done
        ip link show "${interface_name}"
        j=$((j+1))
    done < "${SRIOV_NUMVFS_MAPPINGS}"
}

setup_vfs_mac
