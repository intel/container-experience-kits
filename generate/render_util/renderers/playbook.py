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
This file contains functions needed for playbooks generation
"""

import os
from render_util.common.common import render

_available_playbooks = [ 'access', 'basic', 'full_nfv', 'on_prem', 'on_prem_vss',
                         'on_prem_sw_defined_factory', 'on_prem_aibox', 'remote_fp', 'regional_dc', 'build_your_own']
_playbook_dir = 'playbooks'


def render_playbooks(profile: str) -> None:
    """Renders playbooks for all CEK profiles"""
    # generate playbooks
    if profile not in _available_playbooks:
        _create_all_playbooks()  # profile is set to all_examples
    else:
        _create_playbooks_for_profile(profile)  # specific profile was requested

    # print some usefull information for user at the end
    if profile != 'all_examples':
        _print_command(profile)


def _create_playbook(template_name: str, playbook_file: str, jinja_vars: dict, playbook_subdir: str = '') -> None:
    """Creates one playbook"""
    playbook_path = os.path.join(_playbook_dir, playbook_subdir, playbook_file)
    template_path = os.path.join("generate/playbook_templates", template_name)

    render(template_path, jinja_vars, playbook_path)


def _create_all_playbooks() -> None:
    """Creates all playbooks files"""
    for playbook_name in _available_playbooks:
        _create_playbooks_for_profile(playbook_name)


def _create_playbooks_for_profile(profile: str) -> None:
    """Creates playbooks only for specific profile"""
    playbook_file = profile + ".yml"
    jinja_vars = {"playbook_name": profile}
    _create_playbook("main_playbook.j2", playbook_file, jinja_vars)
    _create_playbook("infra_playbook.j2", playbook_file, jinja_vars, playbook_subdir="infra")
    _create_playbook("intel_playbook.j2", playbook_file, jinja_vars, playbook_subdir="intel")


def _print_command(profile: str) -> None:
    print("""To run your deployment configure host vars and group vars, then use the following command:

    ansible-playbook -i inventory.ini playbooks/{}.yml""".format(profile))
