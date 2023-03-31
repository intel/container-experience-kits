#!/usr/bin/env python

# Copyright (c) 2021 Intel Corporation
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

"""
This file contains functions needed for profile generation in VM mode
"""

import argparse
import os
from render.common.common import create_dir_idempotent, render, load_config, add_arch_parameter, add_nic_parameter, add_mirrors_parameter, create_backups

def render_vm_profiles(args: argparse.Namespace) -> None:
    """Creates example CEK profiles in VM mode"""
    # create backup for already generated profile's hv, gv and inventory
    if 'all_examples' != args.profile:
        src = "./"  # look for reference in project_root_dir
        create_backups(src, ['host_vars', 'group_vars'], ['inventory.ini',])

    # load config from vm_profiles.yml
    vm_profiles = load_config(args.vmsconfig)

    # add architecture information
    add_arch_parameter(vm_profiles, args)

    # add mirrors information
    add_mirrors_parameter(vm_profiles, args)

    # add nic information
    add_nic_parameter(vm_profiles, args)

    # create example diretory with all profiles and its files for VM configuration
    _create_vms_examples(vm_profiles, args)

    # load config for VMs' host
    host_vm_profiles = load_config(args.config)

    # add architecture information
    add_arch_parameter(host_vm_profiles, args)

    # add mirrors information
    add_mirrors_parameter(host_vm_profiles, args)

    # add nic information
    add_nic_parameter(host_vm_profiles, args)

    # create example diretory with all profiles and its files
    _create_host_vm_examples(host_vm_profiles, args)

# Helper Functions
# creating files needed by the VMs
def _create_vm_example(config: dict, vars_path_prefix: str, args: argparse.Namespace) -> None:
    """Create one sample file required by the VM"""
    host_vars_dir_path = os.path.join(vars_path_prefix, "host_vars")
    create_dir_idempotent(host_vars_dir_path)

    render(args.host, config, os.path.join(host_vars_dir_path, "vm-ctrl-1.yml"))
    render(args.host, config, os.path.join(host_vars_dir_path, "vm-work-1.yml"))
    # create another set of configuration files for case that vm_cluster_name is enabled
    render(args.host, config, os.path.join(host_vars_dir_path, "vm-ctrl-1.cluster1.local.yml"))
    render(args.host, config, os.path.join(host_vars_dir_path, "vm-work-1.cluster1.local.yml"))

def _create_vms_examples(profiles: dict, args: argparse.Namespace) -> None:
    """Creates sample configuration files required by the VMs. If profile is marked as all_examples
    then all available examples will be created, otherwise only specific files will be generated into project root directory."""
    if 'all_examples' == args.profile:
        for vms_profile, vms_config in profiles.items():
            vars_path_prefix = os.path.join(args.output, vms_profile)

            _create_vm_example(vms_config, vars_path_prefix, args)
    else:
        vms_profile = args.profile
        vms_config = profiles[vms_profile]
        vars_path_prefix = './'

        _create_vm_example(vms_config, vars_path_prefix, args)

# creating files needed by host on top of which VMs will be created
def _create_host_example(config: dict, vars_path_prefix: str, inventory_path: str, args: argparse.Namespace) -> None:
    """Create one sample file required by host on top of which VMs will be created"""
    host_vars_dir_path = os.path.join(vars_path_prefix, "host_vars")
    group_vars_dir_path = os.path.join(vars_path_prefix, "group_vars")
    create_dir_idempotent(group_vars_dir_path)
    create_dir_idempotent(host_vars_dir_path)

    render(args.host, config, os.path.join(host_vars_dir_path, "host-for-vms-1.yml"))
    config_secondary = dict(config)
    config_secondary['secondary_host'] = 'true'
    render(args.host, config_secondary, os.path.join(host_vars_dir_path, "host-for-vms-2.yml"))
    render(args.group, config, os.path.join(group_vars_dir_path, "all.yml"))

    # do not generate inventory file if already there
    inventory_path = os.path.join(inventory_path, "inventory.ini")
    if not os.path.exists(inventory_path):
        render(args.inventory, config, inventory_path)

def _create_host_vm_examples(profiles: dict, args: argparse.Namespace) -> None:
    """Creates sample configuration files required by host on which the VMs will be created.
        If profile is marked as all_examples then all available examples will be created,
        otherwise only specific files will be generated into project root directory."""
    if 'all_examples' == args.profile:
        for host_vm_profile, host_vm_config in profiles.items():
            vars_path_prefix = os.path.join(args.output, host_vm_profile)
            inventory_path = vars_path_prefix  # inventory file is supposed to be created only with host-related files

            _create_host_example(host_vm_config, vars_path_prefix, inventory_path, args)
        print("\nSample files for all profiles in VM mode are generated to examples directory.")
    else:
        host_vm_profile = args.profile
        vars_path_prefix = './'
        inventory_path = vars_path_prefix

        _create_host_example(profiles[host_vm_profile], vars_path_prefix, inventory_path, args)
        print("\nFiles needed for the '{}' profile are generated in the project root dir.".format(host_vm_profile))
