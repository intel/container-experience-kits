#!/usr/bin/python

# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2022 Intel Corporation

"""
This file contains ansible module check_nic_firmware
"""

from __future__ import (absolute_import, division, print_function)
# Bandit:
# Issue: [B404:blacklist] Consider possible security implications associated with the subprocess module. # pylint: disable=line-too-long
# Severity: Low   Confidence: High
# More Info: https://bandit.readthedocs.io/en/latest/blacklists/blacklist_imports.html#b404-import-subprocess # pylint: disable=line-too-long
# -> considered
import subprocess # nosec B404
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type # pylint: disable=invalid-name

DOCUMENTATION = r'''
---
module: check_nic_firmware

short_description: This module checks current nic firmware version against provided minimum version

version_added: "1.0.0"

description: This module checks current nic firmware version against provided minimum version.
             If current fw version is lower than provided minimum version than module fails.
             It supports ddp flag, which drives the right hints for user.

options:
    pci_id:
        description: This is nic PCI id to be checked.
        required: true
        type: str
    min_fw_version:
        description: Minimal firmware version, which is allowed
        required: true
        type: str
    ddp:
        description:
            - module provides hint what to do when current fw version is not sufficient
            - if ddp is true then version is check for purpose of loading DDP profile
            - if ddp is false then version is check for purpose of automatic firmware update purpose
        required: false
        default: false
        type: bool

author:
    - Jiri Prokes (jirix.prokes@intel.com)
'''

EXAMPLES = r'''
- name: check nic firmware version needed for loading of DDP profile
  check_nic_firmware:
    pci_id: "18:00.1"
    min_fw_version: "6.01"
    ddp: true

- name: check nic firmware version needed for automatic firmware update
  check_nic_firmware:
    pci_id: "18:00.1"
    min_fw_version: "5.02"
'''

RETURN = r'''
# Check succeeded

    "changed": false,
    "interface_pci_id": "18:00.1",
    "interface_name": "enp24s0f1",
    "min_firmware_version": "5.02"
    "current_firmware_version": "8.50",
MSG:
nic firmware version is sufficient to proceed


# Check failed for ddp=true

    "changed": false,
    "interface_pci_id": "18:00.1",
    "interface_name": "enp24s0f1",
    "min_firmware_version": "6.01"
    "current_firmware_version": "5.50",
MSG:
Current nic firmware version doesn't allow loading of DDP profile. Set 'update_nic_firmware' to 'true' and run deployment again.


# Check failed for ddp=false

    "changed": false,
    "interface_pci_id": "18:00.1",
    "interface_name": "enp24s0f1",
    "min_firmware_version": "5.02"
    "current_firmware_version": "4.20",
MSG:
Current nic firmware version is lower than minimum version needed for automatic firmware update. Update nic firmware manually and run deployment again.


# Check failed because of unknown nic name

    "changed": false,
    "interface_pci_id": "18:00.1_wrong",
    "interface_name": "enp24s0f1_wrong",
    "min_firmware_version": "5.02"
    "current_firmware_version": "",
MSG:
Requested nic interface '18:00.1_wrong' with name 'enp24s0f1_wrong' not found. Update 'dataplane_interfaces' accordingly and run deployment again.


# Check failed because of unknown nic

    "changed": false,
    "interface_pci_id": "18:00.1_wrong",
    "interface_name": "",
    "min_firmware_version": "5.02"
    "current_firmware_version": "",
MSG:
Name for the requested nic interface '18:00.1_wrong' not found. Update 'dataplane_interfaces' accordingly and run deployment again.
'''


def run_module():
    """Run Ansible module"""
    module_args = dict(
        pci_id=dict(type='str', required=True),
        min_fw_version=dict(type='str', required=True),
        ddp=dict(type='bool', required=False, default=False)
    )
    encoding = 'utf-8'

    result = dict(
        changed=False,
        failed=False,
        interface_pci_id='',
        interface_name='',
        min_firmware_version='',
        current_firmware_version=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result['interface_pci_id'] = module.params['pci_id']
    result['min_firmware_version'] = module.params['min_fw_version']

    cmd = "find /sys/class/net -mindepth 1 -maxdepth 1 -lname '*" + module.params['pci_id'] + \
          "*' -prune -execdir basename '{}' ';'"
    # Bandit:
    # Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True identified, security issue. # pylint: disable=line-too-long
    # Severity: High   Confidence: High
    # More Info: https://bandit.readthedocs.io/en/latest/plugins/b602_subprocess_popen_with_shell_equals_true.html # pylint: disable=line-too-long
    # -> considered
    nic_name_result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE) # nosec

    if not nic_name_result.stdout:
        module.fail_json(msg="Name for the requested nic interface '" + module.params['pci_id'] +
                             "' not found. Update 'dataplane_interfaces' accordingly and run " +
                             "deployment again.", **result)
    nic_name = str(nic_name_result.stdout.rstrip(), encoding)
    result['interface_name'] = nic_name

    # Bandit:
    # Issue: [B607:start_process_with_partial_path] Starting a process with a partial executable path. # pylint: disable=line-too-long
    # Severity: Low   Confidence: High
    # More Info: https://bandit.readthedocs.io/en/latest/plugins/b607_start_process_with_partial_path.html # pylint: disable=line-too-long
    # -> considered - absolute path can differ on different OS distributions
    #
    # Issue: [B603:subprocess_without_shell_equals_true] subprocess call - check for execution of untrusted input. # pylint: disable=line-too-long
    # Severity: Low   Confidence: High
    # More Info: https://bandit.readthedocs.io/en/latest/plugins/b603_subprocess_without_shell_equals_true.html # pylint: disable=line-too-long
    # -> considered
    sub_result = subprocess.Popen(["ethtool", "-i", nic_name], stdout=subprocess.PIPE) # pylint: disable=consider-using-with # nosec

    if not sub_result.stdout.readline():
        module.fail_json(msg="Requested nic interface '" + module.params['pci_id'] +
                             "' with name '" + nic_name + "' not found. " +
                             "Update 'dataplane_interfaces' accordingly and run deployment again.",
                             **result)

    for line in sub_result.stdout:
        if b'firmware-version' in line:
            result['current_firmware_version'] = str(line.rstrip().split()[1], encoding)
            if float(result['current_firmware_version']) < float(module.params['min_fw_version']):
                if module.params['ddp']:
                    module.fail_json(msg="Current nic firmware version doesn't allow loading of " +
                                         "DDP profile. Set 'update_nic_firmware' " +
                                         "to 'true' and run deployment again.", **result)
                else:
                    module.fail_json(msg="Current nic firmware version is lower than minimum " +
                                         "version needed for automatic firmware update. " +
                                         "Update nic firmware manually and run deployment again.",
                                         **result)
            else:
                result['msg'] = "nic firmware version is sufficient to proceed"
                module.exit_json(**result)

    module.exit_json(**result)


def main():
    """Main function"""
    run_module()


if __name__ == '__main__':
    main()
