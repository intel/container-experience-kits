# Copyright (c) 2017, Intel Corporation.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Intel Corporation nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import pprint

from ansible.plugins.lookup import LookupBase
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

DOCUMENTATION = '''
---
module: check_params
short_description: verifies all the provided parameters
description:
    True value for check FAILURE.

options:
  variables: all the variables that ansible see for deployment
'''

def do_tenant_networks(params):
    check_node_types = ['master', 'minion']
    comp = []
    for hostname, val in params['node_info'].iteritems():
        # we dont need to check control nodes
        if any(node_type in params['hostvars'][hostname]['group_names'] for node_type in check_node_types):
            comp.append(set(val['tenant_networks'].keys()))
    first = comp[0]
    for other in comp:
        if first != other:
            return True
    return False

CHECKS = {
    'tenant_networks': do_tenant_networks,
}

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        check_facts = {}
        for check, call in CHECKS.iteritems():
            check_facts[check] = call(variables)
        return check_facts

