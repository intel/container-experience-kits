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

import argparse

def parse_cli() -> argparse.Namespace:
    """parse_cli creates CLI interface and returns parsed arguments"""
    parser = argparse.ArgumentParser()

    # common args
    parser.add_argument('--config', '-c', type=str, default="k8s_profiles.yml",
        help='path to the profiles configuration file')
    parser.add_argument('--output', type=str, default="../examples/k8s",
        help='directory where generated example files for k8s mode will be stored')
    parser.add_argument('--inventory', type=str, default="k8s_inventory.j2",
        help='inventory template filepath')
    parser.add_argument('--group', '-g', type=str, default="group_vars.j2",
        help='group_vars template filepath')
    parser.add_argument('--host', type=str, default="host_vars.j2",
        help='host_vars template filepath')
    parser.add_argument('--profile', '-p', type=str, default='',
        choices={'all_examples', 'access', 'basic', 'full_nfv', 'on_prem', 'regional_dc', 'remote_fp', 'storage', 'build_your_own'}, # add new profiles here
        help='''profile name which files, required in deployment, will be copied to the project root directory''')
    parser.add_argument('--arch', '-a', type=str, default='icx', choices={"icx", "clx", "skl", "spr"})  # please add acronyms for new architectures here
    parser.add_argument('--nic', '-n', type=str, default='cvl', choices={"cvl", "fvl"})  # please add new NICs here
    parser.add_argument('--mode', type=str, default='k8s', choices={"k8s", "vm", "cloud"}, help='generate configuration files for selected mode')  # please add new modes' name here

    # vm mode specific args
    parser.add_argument('--vmsconfig', type=str, default="vms_profiles.yml", help='configuration file for created Virtual Machine')

    return parser.parse_args()
