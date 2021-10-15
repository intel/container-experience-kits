#!/usr/bin/env python

#
#   Copyright (c) 2020-2021 Intel Corporation.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

"""This module loads BMRA Profiles configuration file and renders example vars
and inventory files using Jinja templates.
"""

import argparse
import os
from shutil import copytree, copy2, rmtree

from ruamel.yaml import YAML
from jinja2 import Template

def load_config(path):
    """Loads YAML file and returns it as dict."""
    with open(path) as config_file:
        yaml = YAML(typ='safe')
        profiles = yaml.load(config_file)
        return profiles

def create_dir_idempotent(path):
    """Creates directory if not present."""
    if not os.path.exists(path):
        os.makedirs(path)

def render(template_path, jinja_vars, target_path):
    """Renders Jinja template and writes it to file."""
    with open(template_path) as file_:
        template = Template(file_.read())
        out = template.render(jinja_vars)
        target_file = open(target_path, "w+")
        target_file.write(out)
        target_file.close()

def copy_file(path_to_file, dest):
    """Copy file to specific destination"""
    copy2(path_to_file, dest)

def copy_dir(src, dst):
    """Copy dir to specific destination"""
    copytree(src, dst)

def copy_dirs(src, dst, dirs_to_copy):
    """Copy given dirs to specific destination"""
    for d in dirs_to_copy:
        path_to_dir = os.path.join(src, d)
        dest_pat = os.path.join(dst, d)
        copy_dir(path_to_dir, dest_pat)

def remove_dir(path_to_dir):
    """Remove directory from specific path"""
    rmtree(path_to_dir, ignore_errors=True)  # don't fail if dir doesn't exist

def remove_dirs(src, dirs):
    """Remove given dirs from specific destination"""
    for d in dirs:
        path_to_dir = os.path.join(src, d)
        remove_dir(path_to_dir)

def prepare_profile(output_dir, profile_name):
    """Remove old and provide new profile's files/dirs.
    Will not override inventory.ini file."""
    src = os.path.join(output_dir, profile_name)

    # determine project root dir location
    project_root_dir = '../' if 'profiles' in os.getcwd() else './'
    dirs = ['host_vars', 'group_vars']
    inventory = 'inventory.ini'

    # clean project root dir from host_vars and group_vars
    remove_dirs(project_root_dir, dirs)

    # obtain newly generated project files
    copy_dirs(src, project_root_dir, dirs)

    # do not override invetory.ini if exists already
    path = os.path.join(project_root_dir, inventory)
    if not os.path.exists(path):
        example_inv_path = os.path.join(src, inventory)
        copy_file(example_inv_path, project_root_dir)

def main():
    """Loads configuration and renders inventory and vars templates."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config', '-c', type=str, default="profiles.yml",
        help='path to the profiles configuration file')
    parser.add_argument('--group', '-g', type=str, default="group_vars.j2",
        help='group_vars template filepath')
    parser.add_argument('--host', type=str, default="host_vars.j2",
        help='host_vars template filepath')
    parser.add_argument('--inventory', '-i', type=str, default="inventory.j2",
        help='inventory template filepath')
    parser.add_argument('--output', '-o', type=str, default="../examples",
        help='directory where generated files will be stored')
    parser.add_argument('--profile', '-p', type=str, default='',
        help='''profile, specified as full profile name 
        e.g. -p full_nfv, which files should be copied to project root dir.
        Only one profile can be specified.''')
    args = parser.parse_args()

    profiles = load_config(args.config)

    for profile, config in profiles.items():
        group_vars_dir_path = os.path.join(args.output, profile, "group_vars")
        host_vars_dir_path = os.path.join(args.output, profile, "host_vars")

        create_dir_idempotent(group_vars_dir_path)
        create_dir_idempotent(host_vars_dir_path)

        render(args.group, config, os.path.join(group_vars_dir_path, "all.yml"))
        render(args.host, config, os.path.join(host_vars_dir_path, "node1.yml"))
        render(args.inventory, config, os.path.join(args.output, profile, "inventory.ini"))

    if args.profile in profiles.keys():
        prepare_profile(args.output, args.profile)
        print("Files needed for {} profile are copied to project root dir.".format(args.profile))
    elif args.profile:
        print("Specified profile does not exist in profiles.yml file. Is there a typo in profile name?")

if __name__ == "__main__":
    main()
