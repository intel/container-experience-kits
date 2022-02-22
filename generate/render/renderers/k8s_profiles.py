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
This file contains functions needed for profile generation in k8s mode
"""

import argparse
import os
from render.common.common import create_dir_idempotent, render, load_config, add_arch_parameter, create_backups

def render_k8s_profiles(args: argparse.Namespace) -> None:
    """Creates example CEK profiles in k8s mode"""
    # create backup for already generated profile's files
    if 'all_examples' != args.profile:
        src = "./"  # look for reference in project_root_dir
        create_backups(src, ['host_vars', 'group_vars'], ['inventory.ini',])

    # load config from k8s_profiles.yml
    k8s_profiles = load_config(args.config)

    # add architecture information
    add_arch_parameter(k8s_profiles, args)

    # create example diretory with all profiles and its files
    _create_k8s_examples(k8s_profiles, args)

# Helper functions
def _create_example(config: dict, vars_path_prefix: str, inventory_path: str, args: argparse.Namespace) -> None:
    group_vars_dir_path = os.path.join(vars_path_prefix, "group_vars")
    host_vars_dir_path = os.path.join(vars_path_prefix, "host_vars")
    create_dir_idempotent(group_vars_dir_path)
    create_dir_idempotent(host_vars_dir_path)

    render(args.group, config, os.path.join(group_vars_dir_path, "all.yml"))
    render(args.host, config, os.path.join(host_vars_dir_path, "node1.yml"))

    # do not generate inventory file if already there
    inventory_path = os.path.join(inventory_path, "inventory.ini")
    if not os.path.exists(inventory_path):
        render(args.inventory, config, inventory_path)

def _create_k8s_examples(profiles: dict, args: argparse.Namespace) -> None:
    """Creates all sample files for profiles in k8s mode if provided profiles is 'all_examples', otherwise
    only files for the specific profile will be generated into project root direcotory"""
    if 'all_examples' == args.profile:
        for k8s_profile, k8s_config in profiles.items():
            vars_path_prefix = os.path.join(args.output, k8s_profile)
            inventory_path = vars_path_prefix

            _create_example(k8s_config, vars_path_prefix, inventory_path, args)
        print("\nSample files for all profiles in K8S mode are generated to examples directory.")
    else:
        k8s_profile = args.profile
        vars_path_prefix = './'
        inventory_path = vars_path_prefix

        _create_example(profiles[k8s_profile], vars_path_prefix, inventory_path, args)
        print("\nFiles needed for the '{}' profile are generated in the project root dir.".format(k8s_profile))
