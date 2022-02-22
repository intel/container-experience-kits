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
This module loads Container Experience Kit Profiles configuration file and renders example vars
and inventory files using Jinja templates.
"""

import argparse
import importlib
from render.common.cli import parse_cli
from render.renderers.playbook import render_playbooks

def main():
    args = parse_cli()

    # render profiles in given mode
    _render_mode(args)

    # render playbooks
    render_playbooks(args.profile)

def _render_mode(args: argparse.Namespace) -> None:
    # determine function name based on passed mode
    mode_to_render = "render_{}_profiles".format(args.mode)

    # determine file name in which desired function is defined and implemented
    renderer = "{}_profiles".format(args.mode)

    # try to import module and then
    # obtain and call required method
    try:
        renderer_module = importlib.import_module("render.renderers.{}".format(renderer), package=None)
        method = getattr(renderer_module, mode_to_render)
        method(args)
    except (ImportError, NameError) as e:
        print("The method '{}' is not defined or cannot be imported... \nError: {}".format(method, e))

if __name__ == "__main__":
    main()
