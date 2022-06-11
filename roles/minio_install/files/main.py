#!/usr/bin/env python3

import ast
from ruamel import yaml

def nostr(d):
    def tr(s):
        s = s.strip()
        try:
            return int(s)
        except ValueError:
            return s

    if isinstance(d, dict):
        for k in d:
            d[k] = nostr(d[k])
        return d
    elif isinstance(d, list):
        for idx, k in enumerate(d):
            d[idx] = nostr(k)
        return d
    return tr(d)

def generate_k8s_service_patch():
    # define text file to open
    my_file = open('parsed-ips-result.txt', 'r')

    # read text file into list
    # data = [word.split(',') for word in open('parsed-ips-result.txt', 'r').readlines()]
    data = my_file.read()

    # display content of text file
    ips = []
    listdata = ast.literal_eval(data)

    for lst in listdata:
        ip = []
        has_name = False
        for str in lst:
            # if str is in ['name', 'ips', 'pod-name']:
            if str == 'name':
                if has_name == True:
                    ips.append(ip)
                ip = []
                has_name = True
            ip.append(str)
        ips.append(ip)
        # copy last 2 elements into previous lists
        num_ips_list = len(ips)
        for x in range(num_ips_list - 1):
            if len(ips[x]) != len(ip):
                ips[x].append(ip[-2])
                ips[x].append(ip[-1])
    # convert to key, value
    result = []
    for lst in ips:
        result.append(dict(zip(lst[::2], lst[1::2])))

    result2 = {}
    result2['ep_data'] = result

    with open("gen-endpoints-data.yaml", "w") as output:
        yaml.safe_dump(nostr(result2), output, indent=4, block_seq_indent=2, allow_unicode=False)
if __name__ == '__main__':
    generate_k8s_service_patch()
