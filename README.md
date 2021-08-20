# Intel Container Experience Kits Setup Scripts

Intel Container Experience Kits Setup Scripts provide a simplified mechanism for installing and configuring Kubernetes clusters on Intel Architecture using Ansible.

The software provided here is for reference only and not intended for production environments.

## Quickstart guide
1. Initialize git submodules to download Kubespray code.
    ```
    git submodule update --init
    ```

1. Decide which configuration profile you want to use and optionally export environmental variable. (Note: It will be used only to ease execution of the steps listed below.)
    - For **Kubernetes Basic Infrastructure** deployment:
    ```
    export PROFILE=basic
    ```
    - For **Kubernetes Access Edge Infrastructure** deployment:
    ```
    export PROFILE=access
    ```
    - For **Kubernetes Regional Data Center Infrastructure** deployment:
    ```
    export PROFILE=regional_dc
    ```
    - For **Kubernetes Remote Forwarding Platform Infrastructure** deployment:
    ```
    export PROFILE=remote_fp
    ```
    - For **Kubernetes Infrastructure On Customer Premises** deployment:
    ```
    export PROFILE=on_prem
    ```
    - For **Kubernetes Full NFV Infrastructure** deployment:
    ```
    export PROFILE=full_nfv
    ```

1. Copy example inventory file to the project root dir.
    ```
    cp examples/${PROFILE}/inventory.ini .
    ```

1. Update inventory file with your environment details.

    Note: at this stage you can inspect your target environment by running:
    ```
    ansible -i inventory.ini -m setup all > all_system_facts.txt
    ```

    In `all_system_facts.txt` file you will find details about your hardware, operating system and network interfaces, which will help to properly configure Ansible variables in the next steps.

1. Copy group_vars and host_vars directories.
    ```
    cp -r examples/${PROFILE}/group_vars examples/${PROFILE}/host_vars .
    ```

1. Update group and host vars to match your desired configuration. Refer to [this section](#configuration) for more details.

    Note: Please pay special attention to the `http_proxy`, `https_proxy` and `additional_no_proxy` vars if you're behind proxy.

1. RECOMMENDED: Apply bug fix patch for Kubespray submodule (Required for RHEL 8+).
    ```
    ansible-playbook -i inventory.ini playbooks/k8s/patch_kubespray.yml
    ```

1. Execute `ansible-playbook`.
    ```
    ansible-playbook -i inventory.ini playbooks/${PROFILE}.yml
    ```

## Configuration

Refer to the documentation linked below to see configuration details for selected capabilities and deployment profiles.

- [SRIOV Network Device Plugin and SRIOV CNI plugin](docs/sriov.md)

## Prerequisites and Requirements
* Python present on the target servers depending on the target distribution. Python 3 is highly recommended, but Python 2 is still supported for CentOS 7.
* Ansible 2.9.20 installed on the Ansible host machine (the one you run these playbooks from).
* python-pip3 installed on the Ansible machine.
* python-netaddr installed on the Ansible machine.
* SSH keys copied to all Kubernetes cluster nodes (`ssh-copy-id <user>@<host>` command can be used for that).
* Internet access on all target servers is mandatory. Proxy is supported.
* At least 8GB of RAM on the target servers/VMs for minimal number of functions (some Docker image builds are memory-hungry and may cause OOM kills of Docker registry - observed with 4GB of RAM), more if you plan to run heavy workloads such as NFV applications.
* For the `RHEL`-like OSes `SELinux` must be configured prior to the BMRA deployment and required `SELinux`-related packages should be installed.
  `BMRA` itself is keeping initial `SELinux` state but `SELinux`-related packages might be installed during `k8s` cluster deployment as a dependency, for `Docker` engine e.g.,
  causing OS boot failure or other inconsistencies if `SELinux` is not configured properly.
  Preferable `SELinux` state is `permissive`.
  For more details, please, refer to the respective OS documentation.
