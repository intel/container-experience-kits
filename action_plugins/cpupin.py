#!/usr/bin/python
#
#   Copyright (c) 2020-2023 Intel Corporation.
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

# Make coding more python3-ish, this is required for contributions to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import random
import copy

from ansible.module_utils._text import to_native
from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleActionFail

# Minimum required vCPUs for the VM
MINIMUM_VCPUS = 4
# Number of vCPUs (CPUs + threads) allocated for host OS
HOST_OS_VCPUS = 16
# Minimum required vCPUs for host OS
MINIMUM_HOST_OS_VCPUS = 2


class ActionModule(ActionBase):
    """cpupin action plugin implementation"""
    def __init__(self, task, connection, play_context, loader, templar, shared_loader_obj):
        super().__init__(task, connection, play_context, loader, templar, shared_loader_obj)
        # CPUs allocated for host OS
        # Example: [[0, 1, 2, 3, 4, 5, 6, 7], [44, 45, 46, 47, 48, 49, 50, 51]]
        # list
        self.host_os_cpus = []
        # Dictionary with all NUMA nodes available on host and their respective CPUs
        # (currently available)
        # Example: {'node0': [[0, 1, ... , 21],[44, 45, ... , 65]], 'node1': [[22, 23, ... , 43],
        #           [66, 67, ... , 87]]}
        # dict
        self.numa_nodes_cpus = {}
        # Dictionary with all NUMA nodes available on host and their respective CPUs
        # Example: {'node0': [[0, 1, ... , 21],[44, 45, ... , 65]], 'node1': [[22, 23, ... , 43],
        #           [66, 67, ... , 87]]}
        # dict
        self.numa_nodes_cpus_orig = {}
        # List of host OS NUMA nodes
        # Example: [0, 1]
        # list
        self.numa_nodes = []
        # Number of unallocated CPUs
        # int
        self.unallocated_cpus = 0
        # Set if some change happened during module run
        # bool
        self.changed = False
        # String with name of VM
        # str
        self.name = None
        # Number of requested CPUs. When number is 0 then it selects rest of CPUs
        # from given numa or max number of CPUs from numa with highest number of available CPUs
        # int
        self.number = None
        # NUMA node which should be used for allocation of CPUs
        # int
        self.numa = None
        # String specifying requested CPU list, compatible with lscpu output
        # Example: '8-9,44-45'
        self.cpus = None
        # Number of requested CPUs for host OS. Default is HOST_OS_VCPUS
        # Those CPU are taken from numa node 0. Minimal number is MINIMUM_HOST_OS_VCPUS
        # int
        self.number_host_os = HOST_OS_VCPUS
        # When it is true then allocate all CPUs and skip numa allignment
        # It works only with number = 0 and undefined cpus and numa
        # bool
        self.alloc_all = False
        # Do we really do CPU pinning, or just allocate CPUs?
        # bool
        self.pinning = False
        # Return values
        # dict
        self.result = {'changed': self.changed,
                       'name': self.name,
                       'number': self.number,
                       'numa': self.numa,
                       'cpus': self.cpus,
                       'number_host_os': self.number_host_os,
                       'alloc_all': self.alloc_all,
                       'pinning': self.pinning}
        # List of lists with allocated CPUs
        # Example: [[8, 9, ...], [44, 45, ...]]
        self.cpu_list = []
        # Number of cpus in list of allocate CPUs (self.cpu_list)
        # int
        self.cpu_list_count = None
        # CPUs selected for emulator pinning
        # Example: [8, 44]
        # list
        self.emu_cpus = []

    def run(self, tmp=None, task_vars=None):
        """Main method"""
        super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()
        self._execute_module(module_name='cpupin',
                             module_args=module_args,
                             task_vars=task_vars, tmp=tmp)

        self.name = self._task.args.get('name', None)
        self.number = self._task.args.get('number', None)
        self.cpus = self._task.args.get('cpus', None)
        self.numa = self._task.args.get('numa', None)
        self.number_host_os = self._task.args.get('number_host_os', HOST_OS_VCPUS)
        self.alloc_all = self._task.args.get('alloc_all', False)
        self.pinning = self._task.args.get('pinning', None)

        # Initialise numa_nodes key
        if 'numa_nodes' not in task_vars:
            task_vars['numa_nodes'] = {}
        # Initialise numa_nodes_cpus key
        if 'numa_nodes_cpus' not in task_vars:
            task_vars['numa_nodes_cpus'] = {}
        # Initialise numa_nodes_cpus_orig key
        if 'numa_nodes_cpus_orig' not in task_vars:
            task_vars['numa_nodes_cpus_orig'] = {}
        # Initialise host_os_cpus key
        if 'host_os_cpus' not in task_vars:
            task_vars['host_os_cpus'] = {}

        msg = ""

        if self.cpus:
            if self.numa is None:
                msg = "'numa' parameter has to be used together with 'cpus' parameter"
            self.result['cpus'] = self.cpus

        if self.name is None:
            msg = "'name' parameter is required"

        if self.pinning is None:
            msg = "'pinning' argument is mandatory"

        if not self.pinning and self.number is None:
            msg = ("You have to configure 'cpu_total' parameter in host_vars file when "
                   "'pinning' parameter is set to 'false'")

        if not self.pinning and int(self.number_host_os) < MINIMUM_HOST_OS_VCPUS:
            msg = (f"Number of CPUs for host OS 'cpu_host_os': {self.number_host_os} have to be "
                   f"at least {MINIMUM_HOST_OS_VCPUS}")

        if not self.pinning and (int(self.number_host_os) % 2) != 0:
            msg = f"Number of CPUs for host OS 'cpu_host_os': {self.number_host_os} have to be even"

        if not self.pinning and self.alloc_all and int(self.number) != 0:
            msg = "You have to set parameter 'cpu_total:' to '0' when 'alloc_all: true' is used"

        if not self.pinning and self.alloc_all and ( self.cpus or self.numa ):
            msg = "'cpus' and 'numa' can't be used with 'alloc_all: true'"

        if self.pinning and not self.alloc_all and (not self.cpus or not self.numa):
            msg = ("When using parameter pinning=true, 'cpus' and 'numa' parameters have to be "
                   "prepared in advance e.g.: via running module with pinning=false")

        if self.pinning and self.alloc_all and (not self.cpus or self.numa):
            msg = ("When using parameters pinning=true and alloc_all=true, 'numa' parameter is None"
                   ", 'cpus' parameter have to be prepared in advance e.g.: via running module with"
                   " pinning=false")

        if self.pinning and self.alloc_all and (not self.cpus or self.numa):
            msg = ("When using parameters pinning=true and alloc_all=true, 'numa' parameter is None"
                ", 'cpus' parameter have to be prepared in advance e.g.: via running module with "
                "pinning=false")

        if msg:
            raise AnsibleActionFail(msg)

        if task_vars['numa_nodes_cpus']:
            self.numa_nodes_cpus = task_vars['numa_nodes_cpus']
        else:
            # Gather hardware information
            if not self.numa_nodes_cpus:
                self._numa_nodes_cpus()
                self.numa_nodes_cpus_orig = copy.deepcopy(self.numa_nodes_cpus)
            task_vars['numa_nodes_cpus'] = self.numa_nodes_cpus
            task_vars['numa_nodes_cpus_orig'] = self.numa_nodes_cpus_orig
            task_vars['numa_nodes'] = self.numa_nodes

        if task_vars['numa_nodes_cpus_orig']:
            self.numa_nodes_cpus_orig = task_vars['numa_nodes_cpus_orig']

        if task_vars['numa_nodes']:
            self.numa_nodes = task_vars['numa_nodes']

        if task_vars['host_os_cpus']:
            self.host_os_cpus = task_vars['host_os_cpus']

        if not self.pinning:
            # Run sanity checks
            self._sanity_checks(task_vars)
            if self.alloc_all:
                task_vars = self._allocate_all_cpus(task_vars)
            else:
                task_vars = self._allocate_cpus(task_vars)
            self._cpus_list_to_string()
        else:
            self.result['pinning'] = self.pinning
            self.cpu_list = self._create_plain_cpu_list(self.cpus)
            self.cpu_list_count = len(self.cpu_list)
            self.number = self.cpu_list_count
            self._select_emu_cpus()
            self._pin_cpus()

        self.result['number'] = int(self.number)
        self.result['name'] = self.name
        self.result['numa'] = self.numa
        self.result['number_host_os'] = int(self.number_host_os)
        self.result['alloc_all'] = self.alloc_all
        return dict(self.result)

    def _sanity_checks(self, task_vars):
        """Sanity checks of input values.

            Input values: @self.number
                          @self.cpus
                          @self.numa
                          @self.pinning
                          @task_vars
            Return value: @task_vars/AnsibleActionFail()
        """
        kwargs = {'number': self.number,
                  'cpus': self.cpus,
                  'numa': self.numa,
                  'pinning': self.pinning
                  }

        msg = ""

        # Number of vCPUs can't be odd. It has to be even
        if kwargs['number'] and (int(kwargs['number']) % 2) != 0:
            msg = "Requested number of VCPUs have to be even"

        # Number of vCPUs can't be lower than MINIMUM_VCPUS
        if kwargs['number'] and int(kwargs['number']) > 0 and int(kwargs['number']) < MINIMUM_VCPUS:
            msg = f"You have to allocate at least {MINIMUM_VCPUS} vCPUs"

        # number of requested CPUs
        if kwargs['number']:
            task_vars = self._allocate_host_os_cpus(task_vars)
            self.numa_nodes_cpus = task_vars['numa_nodes_cpus']
            # Calculate number of unallocated CPUs
            if not self.alloc_all:
                self._number_of_unallocated_host_cpus(self.numa)
                if int(kwargs['number']) == 0:
                    self.number = self.unallocated_cpus
            if int(kwargs['number']) > self.unallocated_cpus:
                msg_detail = ""
                if self.numa is not None:
                    msg_detail = " for selected numa node " + str(self.numa)
                else:
                    msg_detail = " for numa node with the most available CPUs"
                msg = (f"Requested number of CPUs {int(kwargs['number'])} is higher than available"
                       f" number on host {self.unallocated_cpus}{msg_detail}")

        if kwargs['cpus']:
            # Try to split using comma
            split_cpus = kwargs['cpus'].split(',')
            if len(split_cpus) < 2:
                msg = "You have to specify cpus parameter in lscpu format: e.g.: '8-9,44-45'"
            else:
                # Calculate number of vCPUs
                self.cpu_list = self._create_plain_cpu_list(kwargs['cpus'])
                self.cpu_list_count = len(self.cpu_list)
                if self.cpu_list_count < MINIMUM_VCPUS:
                    msg = f"You have to allocate at least {MINIMUM_VCPUS} vCPUs"
                # Verify that list of CPUs equals parameter 'number'
                if kwargs['number']:
                    if self.cpu_list_count != int(kwargs['number']):
                        msg = ("Count of CPUs provided in 'cpus:' list doesn't match number "
                               "specified by 'cpu_total:'")

                # Are CPUs on same NUMA node and correct one?
                if not self._cpus_use_same_numa():
                    msg = "CPUs must be on the same NUMA node, specified by parameter 'numa'"
                # Make sure we are not using CPUs allocated for host OS
                if self._host_os_cpus_used():
                    msg_details = self._host_os_cpus_to_string()
                    msg = f"CPUs can't be from range allocated for host OS '{msg_details}'"
                # Make sure we are not using CPUs, which were already allocated for other VMs
                if self._check_if_cpus_is_used():
                    cpus_details = self._plain_cpus_list_to_string(self.cpu_list)
                    msg = f"Requested CPUs '{cpus_details}' overlap with already allocated CPUs"
        if msg:
            raise AnsibleActionFail(msg)

    def _create_plain_cpu_list(self, cpus_str):
        """Get the string with cpus like '8-9,44-45' and convert it to the list
           of CPUs like '[8,9,44,45]]'

           Input values: @cpu_string
           Return value: @plain_cpu_list
        """
        plain_cpu_list = []
        for cpus in cpus_str.split(','):
            cpus = cpus.split('-')
            if len(cpus) == 1:
                plain_cpu_list += list(range(int(cpus[0]), int(cpus[0]) + 1))
            else:
                plain_cpu_list += list(range(int(cpus[0]), int(cpus[1]) + 1))
        return plain_cpu_list

    def _numa_nodes_cpus(self):
        """Collect information about all NUMA nodes CPUs

            Input values: N/A
            Return values: True/@self.result
        """
        lscpu_result = self._low_level_execute_command("lscpu -p")

        if lscpu_result['rc'] != 0:
            self.result['failed'] = True
            self.result['msg'] = ("lscpu command failed. Error was: "
                                  f"'{to_native(lscpu_result['stdout'].strip())}, "
                                  f"{to_native(lscpu_result['stderr'].strip())}'")
            return self.result
        lscpu_stdout = lscpu_result['stdout']

        pattern = "(\\d+),(\\d+),\\d+,(\\d+),.*"
        result = re.findall(pattern, lscpu_stdout)
        self._create_numa_node_cpus_data_structure(result)
        self.numa_nodes = len(self.numa_nodes_cpus)
        self.numa_nodes = list(range(0, self.numa_nodes))
        return True

    def _create_numa_node_cpus_data_structure(self, data):
        """ From input data create self.numa_nodes_cpus structure

            Input value: @data
            Return value: @self.numa_nodes_cpus
        """
        core_count = 0
        for item in data:
            cpu = item[0]
            core = item[1]
            numa = f"node{item[2]}"

            if numa not in self.numa_nodes_cpus:
                self.numa_nodes_cpus[numa] = [[], []]
            # CPU
            if cpu == core:
                self.numa_nodes_cpus[numa][0].append(int(cpu))
                core_count += 1
            # Thread
            elif cpu == str(int(core) + core_count):
                self.numa_nodes_cpus[numa][1].append(int(cpu))
            else:
                msg = "Unsupported CPU core structure -> lscpu -p"
                raise AnsibleActionFail(msg)

    def _cpus_use_same_numa(self):
        """Make sure that all CPUs are using same NUMA node, specified by 'numa'

            Input values: @self.cpu_list
                          @self.numa
            Return value: True/False
        """
        node = f"node{self.numa}"
        for cpu in self.cpu_list:
            if ((cpu not in self.numa_nodes_cpus_orig[node][0]) and
                    (cpu not in self.numa_nodes_cpus_orig[node][1])):
                return False
        return True

    def _host_os_cpus_used(self):
        """Make sure that requested CPUs are not from list allocated for host OS

           Input value: @self.cpu_list
           Return value: True/False
        """
        for cpu in self.cpu_list:
            if cpu in self.host_os_cpus:
                return True
        return False

    def _check_if_cpus_is_used(self):
        """Make sure that requested CPUs are not from list allocated for other VMs

           Input value: @self.cpu_list
           Return value: True/False
        """
        node = f"node{self.numa}"
        for cpu in self.cpu_list:
            if ((cpu not in self.numa_nodes_cpus[node][0]) and
                    (cpu not in self.numa_nodes_cpus[node][1])):
                return True
        return False

    def _allocate_host_os_cpus(self, task_vars):
        """ Allocate HOST_OS_VCPUS vCPUs for host OS

            Input values: @task_vars
            Return value: @task_vars
        """
        if not self.host_os_cpus:
            self.host_os_cpus = self._select_cpus(task_vars['numa_nodes_cpus'], self.number_host_os, 0)
            self._modify_available_host_cpus(self.host_os_cpus, 0, task_vars['numa_nodes_cpus'])
            task_vars['host_os_cpus'] = self.host_os_cpus
        return task_vars

    def _number_of_unallocated_host_cpus(self, numa):
        """Count unallocated host CPUs

           Input values: numa
           Return number of unallocated host CPUs for corresponding NUMA node.
         If NUMA node is not specified then be AWARE, counting just NUMA node with highest
         available number of unallocated CPUs will be returned.
         If any numa node have less unallocated CPUs than requested then NUMA node with sufficient
         amount of unallogated CPUs is forced.
         We can't mix NUMA nodes CPUs allocations"""
        tmp = 0
        if numa is not None:
            node = f"node{numa}"
            val = self.numa_nodes_cpus[node]
            tmp = len(val[0]) + len(val[1])
            self.unallocated_cpus = tmp
        else:
            tmp_numa = None
            tmp_count = None
            force_numa = False
            if int(self.number) == 0:
                force_numa = True
            for k, val in self.numa_nodes_cpus.items():
                tmp = len(val[0]) + len(val[1])
                if tmp >= int(self.number):
                    tmp_numa = k.strip("node")
                    tmp_count = tmp
                else:
                    force_numa = True

                if tmp > self.unallocated_cpus:
                    self.unallocated_cpus = tmp
            if force_numa:
                if tmp_numa:
                    self.numa = tmp_numa
                    self.unallocated_cpus = tmp_count

    def _allocate_all_cpus(self, task_vars):
        """ Allocate all CPUs

            Input value: @task_vars
            Return value: @task_vars
        """
        for numa in self.numa_nodes:
            self._number_of_unallocated_host_cpus(numa)
            tmp_cpu_list = self._select_cpus(task_vars['numa_nodes_cpus'], self.unallocated_cpus, numa)
            self._modify_available_host_cpus(tmp_cpu_list, numa, task_vars['numa_nodes_cpus'])
            self.cpu_list += tmp_cpu_list
            self.number = int(self.number) + int(self.unallocated_cpus)
        self.result['numa'] = None
        # Check if number of allocated vCPUs isn't lower than MINIMUM_VCPUS
        if int(self.number) < MINIMUM_VCPUS:
            msg = (f"Number of allocated CPUs {self.number} is less than required minimum "
                   f"{MINIMUM_VCPUS} vCPUs")
            raise AnsibleActionFail(msg)
        self.cpu_list.sort()
        return task_vars


    def _allocate_cpus(self, task_vars):
        """ Allocate required number of CPUs

            Input value: @task_vars
            Return value: @task_vars
        """

        # Select random NUMA
        if not self.numa:
            self.numa = random.choice(self.numa_nodes) # nosec B311 # pseudo random is not used for security purposes

        if not self.cpus:
            self.cpu_list = self._select_cpus(task_vars['numa_nodes_cpus'], self.number, self.numa)
        else:
            if self.cpu_list_count == 0:
                self.cpu_list = self._create_plain_cpu_list(self.cpus)
                self.cpu_list_count = len(self.cpu_list)
        self._modify_available_host_cpus(self.cpu_list, self.numa, task_vars['numa_nodes_cpus'])
        self.result['numa'] = self.numa
        return task_vars

    def _select_cpus(self, numa_nodes_cpus, cpus_number, numa):
        """ Select requested number of CPUs from NUMA node

            Input values: @task_vars['numa_nodes_cpus']
                          @cpus_number
                          @numa
            Return values: selected_cpus
        """

        selected_cpus = []
        node = f"node{numa}"
        req_cpus = int(cpus_number) / 2
        sel_cpus = list(numa_nodes_cpus[node][0][0:int(req_cpus)])
        selected_cpus += sel_cpus

        sel_threads = list(numa_nodes_cpus[node][1][0:int(req_cpus)])
        selected_cpus += sel_threads
        return selected_cpus

    def _modify_available_host_cpus(self, requested_cpus, requested_numa, task_vars):
        """ Modify dictionary with available cpus on host

            Input values: @requested_cpus
                          @requested_numa
                          @task_vars['numa_nodes_cpus']
            Return_value: @task_vars['numa_nodes_cpus']
        """
        node = f"node{requested_numa}"
        if len(requested_cpus) > 1:
            tmp_l = requested_cpus
            # Going through host_cpus and delete requested cpus
            for lst in task_vars[node]:
                for item in tmp_l:
                    if item in lst:
                        # remove item
                        lst.remove(item)
        return task_vars

    def _plain_cpus_list_to_string(self, cpu_list):
        """ From input CPUs list create string

            Input values: @cpu_list
            Return value: @cpu_string
        """
        cpu_string = ""
        cpu_string += str(cpu_list[0])
        begin_index = 0
        for i in range(1, len(cpu_list)):
            if cpu_list[i] != cpu_list[i - 1] + 1:
                if i > begin_index + 1:
                    cpu_string += str('-')
                    cpu_string += str(cpu_list[i - 1])
                cpu_string += str(',')
                cpu_string += str(cpu_list[i])
                begin_index = i
            else:
                if i == len(cpu_list) - 1:
                    cpu_string += str('-')
                    cpu_string += str(cpu_list[i])

        return cpu_string

    def _cpus_list_to_string(self):
        """ From input CPUs list create string

            Input values: @self.cpu_list
            Return value: @self.result['cpus']
        """
        cpu_string = self._plain_cpus_list_to_string(self.cpu_list)
        self.result['cpus'] = cpu_string

    def _host_os_cpus_to_string(self):
        """ From input CPUs list of lists create printable string compatible with lscpu output

            Input values: @self.host_os_cpus
            Return value: @string
        """
        host_os_cpu_string = self._plain_cpus_list_to_string(self.host_os_cpus)
        return host_os_cpu_string

    def _select_emu_cpus(self):
        """ Select CPUs for emulator

            Input value: @self.cpu_list
            Return value: @self.emu_cpus
        """
        self.emu_cpus = [self.cpu_list[0], self.cpu_list[int(self.cpu_list_count / 2)]]

    def _pin_cpus(self):
        """ PIN selected cpus for VM usage

            Input values: @self.cpu_list
                          @self.emu_cpus
                          @self.numa
                          @self.name
            Return value: @self.result
        """
        cpu_list = self.cpu_list

        # Convert emu_cpus from list to string
        emu_cpus = ",".join(map(str, self.emu_cpus))

        self.result['failed'] = False
        # Update VM emulator pinning
        for cpu in cpu_list:
            index = str(cpu_list.index(cpu))
            cmd_cpupin = f"virsh vcpupin {self.name} {index} {cpu} --live --config"
            cpupin_result = self._low_level_execute_command(cmd_cpupin)
            # In case of problem
            if cpupin_result['rc'] != 0:
                self.result['failed'] = True
                self.result['msg'] = ("CPU pinning command failed. Error was: "
                                      f"'{to_native(cpupin_result['stdout'].strip())}, "
                                      f"{to_native(cpupin_result['stderr'].strip())}'")

        # Update VM emulator pinning
        cmd_emupin = f"virsh emulatorpin {self.name} {emu_cpus} --live --config"
        emupin_result = self._low_level_execute_command(cmd_emupin)
        if emupin_result['rc'] != 0:
            self.result['failed'] = True
            self.result['msg'] = ("Emulator pinning command failed. Error was: "
                                  f"'{to_native(emupin_result['stdout'].strip())}, "
                                  f"{to_native(emupin_result['stderr'].strip())}'")

        if not self.alloc_all:
        # Update VM NUMA alignment
            cmd_numa = f"virsh numatune {self.name} --nodeset {self.numa} --live --config"
            numa_result = self._low_level_execute_command(cmd_numa)
            if numa_result['rc'] != 0:
                self.result['failed'] = True
                self.result['msg'] = ("NUMA alignment command failed. Error was: "
                                      f"'{to_native(numa_result['stdout'].strip())}, "
                                      f"{to_native(numa_result['stderr'].strip())}'")

        self.result['changed'] = True
