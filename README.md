# Intel Container Experience Kits Setup Scripts

Intel Container Experience Kits Setup Scripts provide a simplified mechanism for installing and configuring Kubernetes clusters on Intel Architecture using Ansible.

## Quickstart guide
1. Initialize git submodules to download Kubespray code.
```
git submodule update --init
```

2. Decide which deployment profile you want to use and optinonally export environmental variable. (Note: It will be used only for easier execution of below steps.)
- For **Advanced** deployment:
```
export PROFILE=advanced
```

3. Copy example inventory file to the project root dir.
```
cp examples/${PROFILE}/inventory.ini .
```

4. Update inventory file with your environment details.

Note: at this stage you can inspect your target environment by running:
```
ansible -i inventory.ini -m setup all > all_system_facts.txt
```
In `all_system_facts.txt` file you will find details about your hardware, operating system and network interfaces, which will help to properly configure Ansible variables in the next steps.


5. Copy group_vars and host_vars directories.
```
cp -r examples/${PROFILE}/group_vars examples/${PROFILE}/host_vars .
```

6. Update group and host vars to match your desired configuration. Refer to [this section](#configuration) for more details.

Note: Please pay special attention to the `http_proxy`, `https_proxy` and `additional_no_proxy` vars if you're behind proxy.

7. Execute `ansible-playbook`.
```
ansible-playbook -i inventory.ini playbooks/${PROFILE}.yml
```

## Configuration

Refer to the documentation linked below to see configuration details for selected capabilities and deployment profiles.

- [SRIOV Network Device Plugin and SRIOV CNI plugin](docs/sriov.md)

## Requirements
* Python 2 present on the target servers.
* Ansible 2.7.16 installed on the Ansible machine (the one you run these playbooks from).
* pip==9.0.3 installed on the Ansible machine.
* SSH keys copied to all Kubernetes cluster nodes (`ssh-copy-id <user>@<host>` command can be used for that).
* Internet access on all target servers is mandatory. Proxy is supported.
* At least 8GB of RAM on the target servers/VMs for minimal number of functions (some Docker image builds are memory-hungry and may cause OOM kills of Docker registry - observed with 4GB of RAM), more if you plan to run heavy workloads such as NFV applications.