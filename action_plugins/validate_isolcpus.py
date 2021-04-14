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
from ansible.plugins.action import ActionBase

def parse_range(cpu_range):
    if '-' in cpu_range:
        [x, y] = cpu_range.split('-')
        cpus = range(int(x), int(y)+1)
        if int(x) >= int(y):
            raise ValueError("incorrect cpu range: " + cpu_range)
    else:
        cpus = [int(cpu_range)]
    return cpus

def parse_cpu_ranges(isolcpus):
    ranges = isolcpus.split(',')
    isolated = []
    for r in ranges:
        isolated += parse_range(r)
    return isolated

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False
        result['failed'] = False

        requested = task_vars['isolcpus']
        present = task_vars['cpus_present']

        try:
            all_cpus = parse_cpu_ranges(present)
            isolcpus = parse_cpu_ranges(requested)
            for cpu in isolcpus:
                if cpu not in all_cpus:
                    raise ValueError("requested isolated cpu is not available on the system: " + str(cpu))
        except Exception as e:
            result['failed'] = True
            result['msg'] = str(e)

        return result
