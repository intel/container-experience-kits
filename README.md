# Intel Container Environment Setup Scripts

Intel Container Environment Setup Sctipts provide a simplified mechanism for installing and configuring Kubernetes on Intel Architecture using Ansible.

## Quickstart guide
1. Initialize git submodules to download Kubespray code.
```
git submodule update --init
```

2. Copy example inventory file to the project root dir.
```
cp examples/inventory.ini .
```

3. Update inventory file with your environment details.

Note: at this stage you can inspect your target environment by running:
```
ansible -i inventory.ini -m setup all  > all_system_facts.txt
```
In `all_system_facts.txt` file you will find details about your hardware, operating system and network interfaces, which will help to properly configure Ansible variables in the next steps.


4. Copy group\_vars and host\_vars directories.
```
cp -r examples/group_vars examples/host_vars .
```

5. Update group and host vars to match your desired configuration.

Note: Please pay special attention to the `http_proxy`, `https_proxy` and `no_proxy` vars in the `proxy_env` dictionary if your behind proxy. Don't forget to add all cluster nodes IP addresses to the `no_proxy` to avoid many potential problems!

6. Execute `ansible-playbook`.
```
ansible-playbook -i inventory.ini playbooks/cluster.yml
```

## Requirements
* Python 2 present on the target servers.
* Ansible 2.7.1 (or newer) installed on the Ansible machine (the one you run these playbooks from).
* pip==9.0.3 installed on the Ansible machine.
* SSH keys copied to all Kubernetes cluster nodes (`ssh-copy-id <user>@<host>` command can be used for that).
* Internet access on all target servers is mandatory. Proxy is supported.
* At least 8GB of RAM on the target servers/VMs for minimal number of functions (some Docker image builds are memory-hungry and may cause OOM kills of Docker registry - observed with 4GB of RAM), more if you plan to run heavy workloads such as NFV applications.
