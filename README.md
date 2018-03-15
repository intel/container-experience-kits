Intel Container Environment Setup Scripts
============================================

Intel Container Environment Setup Sctipts provide a simplified mechanism for installing and configuring Kubernetes on Intel Architecture using Ansible.

Preparing Kubernetes bare-metal nodes using Ansible
============================================

Ansible is a configuration management utility.  It runs on a system separate from the Kubernetes nodes to configure networking, drivers and handle system reboots.

Instructions in this readme have been tested with Ansible version 2.3.1+(<2.4.x).

1. Install Ansible 2.3.1+(<2.4.0) on a deployment system (VM or physical) separate from the nodes to be used for deployment.
   Do not use Ansible 2.4.x

2. Have multiple systems with fresh installations of chosen OS standing by.

3. On the deployment system, create a file in the Ansible directory called ``inventory.ini`` copied from ``examples/inventory.ini``.
   This file holds information regarding which system(s) are master or minions.
   Group vars are used to specify login credentials.  Alternatively, a pre-shared ssh key can be used.  See examples below.

    Inventory hostnames MUST MATCH EXACTLY what is provided by DHCP or DNS.  Ansible does not support case-insentive hostnames.

        [master]
        # Only use 'ansible_host' here to set IP if DNS is not configured
        # The hostname must match the hostname in the ``node_info`` section in deploy.yml (details in subsequent section of this readme)
        # This hostname will be set on the node
        master-1  ansible_host=1.2.3.a

        [minion]
        minion-1  ansible_host=1.2.3.c
        # Optionally, per node passwords are supported
        minion-2  ansible_host=1.2.3.d ansible_ssh_pass=something_different

        [master:vars]
        ansible_user=root
        ansible_ssh_pass=mypass

        [minion:vars]
        ansible_user=root
        ansible_ssh_pass=mypass

        # Or, use the global group 'all' (or -k to provide a password on the command line)
        [all:vars]
        ansible_user=root
        ansible_ssh_pass=mypass

    Only one method of supplying login credentials should be chosen.
    See also http://docs.ansible.com/ansible/intro_inventory.html
    A skeleton of the inventory file can be found in ansible/examples directory.

4. Use Ansible to probe systems and gather facts about network topology for Kolla systems.
   This is a reference file for facts about your deployment. The file itself is not used during deployment.

        ansible -i inventory.ini -m setup all  > all_system_facts.txt

    Examine all_system_facts.txt to get all current network topology details.
    e.g.


        "ansible_interfaces": [
            "ens785f0",
            "lo",
            "ens785f2",
            "ens785f3",
            "ens513f1",
            "ens513f0",
            "mgmt",
            "virtual-1",
            "inter",
            "virbr0-nic",
            "virbr0"
        ],
        "ansible_ens513f1": {
            "active": false,
            "device": "ens513f1",
            "macaddress": "00:1e:67:e2:6f:25",
            "module": "ixgbe",
            "mtu": 1500,
            "promisc": false,
            "type": "ether"
        },
        "ansible_ens785f0": {
            "active": false,
            "device": "ens785f0",
            "macaddress": "68:05:ca:37:dc:68",
            "module": "i40e",
            "mtu": 1500,
            "promisc": false,
            "type": "ether"
        },

5. Modify and copy from ``examples/deploy_...`` to ansible directory.
    - Info regarding available options are outlined as comments in ``groups_vars/all/all/yml``.
    - Using info in all_system_facts.txt, set interface names for mgmt (management), inter (internet), and tenant networks.
    - Define static IPs for interfaces that need them (mgmt ip_address typically) in ``node_info`` section.
      All nodes are configured in parallel, every node has to know the full topology and IP address of every other node.


6. Set ANSIBLE_LOG_BASE environment variable to a desired log path.
   Provide inventory.ini
   Provide deploy.yml as extra_vars
   Run the multinode.yml playbook.

        # export ANSIBLE_LOG_BASE=/tmp/logs/$(date +%Y%m%d%H%M%S)
        # export ANSIBLE_LOG_PATH=$(ANSIBLE_LOG_BASE)/multinode.log

        # ansible-playbook -i inventory.ini -e @deploy.yml multinode.yml


7. Logs from the playbook run will be copied from system to the log path specified (ANSIBLE_LOG_BASE).

Misc
----

   1. If missing, set **kubeconfig** environment variable

      ``export KUBECONFIG=/etc/kubernetes/admin.conf``

   2. Kubernetes status

      ``kubectl get pods --all-namespaces -o wide``

   3. Kubernetes pod stuck in ContainerCreating

      **note:** kube-dns can take a while to go into running state but if needed, delete the pod and kubernets will recreate it

      ``kubectl delete -n kube-system pods {name of pod}``
      
      ``kubectl delete -n kube-system pods kube-dns-545bc4bfd4-jh2xb``
