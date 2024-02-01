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
This file contains common functions used to generate profiles in different modes
"""

import argparse
import os
from datetime import datetime
from shutil import move, copy

from ruamel.yaml import YAML
from jinja2 import Environment, FileSystemLoader


def load_config(path: str) -> dict:
    """Loads YAML file and returns it as configuration dict."""
    with open(path) as config_file:
        yaml = YAML(typ='safe')
        profiles = yaml.load(config_file)
        return profiles


def create_dir_idempotent(path: str) -> None:
    """Creates directory if not present."""
    if not os.path.exists(path):
        os.makedirs(path)


def render(template_path: str, jinja_vars: dict, target_path: str) -> None:
    """Renders Jinja template and writes it to file."""
    file_loader = FileSystemLoader('.')
    template = Environment(keep_trailing_newline=True, trim_blocks=True, loader=file_loader, autoescape=True).get_template(template_path)
    out = template.render(jinja_vars)
    with open(target_path, "w+") as f:
        f.write(out)


def add_arch_parameter(profiles: dict, args: argparse.Namespace) -> None:
    """Add architecture information to profiles config"""
    for p in profiles.values():
        p['arch'] = args.arch


def add_nic_parameter(profiles: dict, args: argparse.Namespace) -> None:
    """Add NIC information to profiles config"""
    for p in profiles.values():
        p['nic'] = args.nic


def add_mirrors_parameter(profiles: dict, args: argparse.Namespace) -> None:
    """Add mirrors information to profiles config"""
    for p in profiles.values():
        p['mirrors'] = args.mirrors


def create_backups(src: str, dirs: list = None, files: list = None) -> None:
    """Create backup for given dirs/files"""
    # create specific backup dir
    if dirs is None:
        dirs = []
    if files is None:
        files = []

    previous_profile_name = _get_previous_profile_name()
    if previous_profile_name:
        backup_dir_name = previous_profile_name + "_" + datetime.now().strftime('%Y%m%d_%H%M%S')
        path_to_backup_dir = os.path.join('backups', backup_dir_name)
        create_dir_idempotent(path_to_backup_dir)

        for d in dirs:
            _backup_dirs(src, path_to_backup_dir, d)

        for f in files:
            _backup_files(src, path_to_backup_dir, f)


# Helper Functions
def _move(path_to_dir: str, path_to_backup_dir: str) -> None:
    """Move directory from specific path to backup path"""
    move(path_to_dir, path_to_backup_dir)


def _backup_dirs(src: str, dst: str, name: str) -> None:
    path = os.path.join(src, name)
    if os.path.exists(path):
        _move(path, dst)


def _backup_files(src: str, dst: str, name: str) -> None:
    path = os.path.join(src, name)
    if os.path.exists(path):
        print(path)
        copy(path, dst)


def _get_previous_profile_name() -> str:
    group_vars_path = os.path.join('./', 'group_vars', 'all.yml')
    if os.path.exists(group_vars_path):
        with open(group_vars_path) as f:
            for line in f:
                if 'profile_name:' in line:
                    name = line.split()[1]
                    return name

    # project root directory is clean
    return ""
