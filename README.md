PROJECT NOT UNDER ACTIVE MANAGEMENT

This project will no longer be maintained by Intel.

This project has been identified as having known security escapes.

Intel has ceased development and contributions including, but not limited to, maintenance, bug fixes, new releases, or updates, to this project.  

Intel no longer accepts patches to this project.
# Intel Container Experience Kits Setup Scripts

Intel Container Experience Kits Setup Scripts provide a simplified mechanism for installing and configuring Kubernetes clusters on Intel Architecture using Ansible.

The software provided here is for reference only and not intended for production environments.

## Information About Release v24.01.1

The most recent patch release, v24.01.1, is mainly for supporting the `on_prem_aibox` profile.

If any issues are observed when using this release for other profiles, please revert to using v24.01 instead.

## Quickstart guide

**_NOTE:_** Instruction provided bellow are prepared for deployment done under root user by default. If you want to do deployment under non-root user then read [this](docs/rootless_deployment.md) file first and then continue with following steps under that non-root user.

1. Decide which configuration profile you want to use and export environmental variable.
   > **_NOTE:_** It will be used only to ease execution of the steps listed below.
    - For **Kubernetes Basic Infrastructure** deployment:

        ```bash
        export PROFILE=basic
        ```

    - For **Kubernetes Access Edge Infrastructure** deployment:

        ```bash
        export PROFILE=access
        ```

    - For **Kubernetes Edge Ready Infrastructure** deployment:

        ```bash
        export PROFILE=base_video_analytics
        ```

    - For **Kubernetes Regional Data Center Infrastructure** deployment:

        ```bash
        export PROFILE=regional_dc
        ```

    - For **Kubernetes Remote Central Office-Forwarding Configuration** deployment:

        ```bash
        export PROFILE=remote_fp
        ```

    - For **Kubernetes Infrastructure On Customer Premises** deployment:

        ```bash
        export PROFILE=on_prem
        ```

    - For **Kubernetes Infrastructure On Customer Premises for VSS** deployment:

        ```bash
        export PROFILE=on_prem_vss
        ```

    - For **Kubernetes Infrastructure On Customer Premises for AI Box** deployment:

        ```bash
        export PROFILE=on_prem_aibox
        ```

    - For **Kubernetes Infrastructure On Customer Premises for SW-Defined Factory** deployment:

        ```bash
        export PROFILE=on_prem_sw_defined_factory
        ```

    - For **Kubernetes Build-Your-Own Infrastructure** deployment:

        ```bash
        export PROFILE=build_your_own
        ```

2. Install python dependencies using one of the following methods

   > **_NOTE:_** Ensure that at least python3.9 is installed on ansible host

    a) Non-invasive virtual environment using pipenv

    ```bash
    pip3 install pipenv
    pipenv install
    # Then to run and use the environment
    pipenv shell
    ```

    b) Non-invasive virtual environment using venv

    ```bash
    python3 -m venv venv
    # Then to activate new virtual environment
    source venv/bin/activate
    # Install dependencies in venv
    pip3 install -r requirements.txt
    ```

    c) System wide environment (not recommended)

    ```bash
    pip3 install -r requirements.txt
    ```

3. Install ansible collection dependencies with following command:

    ```bash
    ansible-galaxy install -r collections/requirements.yml
    ```

4. Copy SSH key to all Kubernetes nodes or VM hosts you are going to use.

    ```bash
    ssh-copy-id <user>@<host>
    ```

5. Generate example host_vars, group_vars and inventory files for Intel Container Experience Kits profiles.

   > **_NOTE:_** It is **highly recommended** to read [this](docs/generate_profiles.md) file before profiles generation.

    Architecture and Ethernet Network Adapter type can be auto-discovered:
    ```bash
    make auto-examples HOSTS=X.X.X.X,X.X.X.X USERNAME=<user>
    ```
    or specified manually:
    ```bash
    make examples ARCH=<atom,core,icx,**spr**,emr,gnr,ultra> NIC=<fvl,**cvl**>
    ```

6. Copy example inventory file to the project root dir.

    ```bash
    cp examples/k8s/${PROFILE}/inventory.ini .
    ```

    or, for VM case:

    ```bash
    cp examples/vm/${PROFILE}/inventory.ini .
    ```

7. Update inventory file with your environment details.

    For VM case: update details relevant for vm_host

    > **_NOTE:_** At this stage you can inspect your target environment by running:

    ```bash
    ansible -i inventory.ini -m setup all > all_system_facts.txt
    ```

    In `all_system_facts.txt` file you will find details about your hardware, operating system and network interfaces, which will help to properly configure Ansible variables in the next steps.

8. Copy group_vars and host_vars directories to the project root dir.

    ```bash
    cp -r examples/k8s/${PROFILE}/group_vars examples/k8s/${PROFILE}/host_vars .
    ```

    or, for VM case:

    ```bash
    cp -r examples/vm/${PROFILE}/group_vars examples/vm/${PROFILE}/host_vars .
    ```

9. Update group and host vars to match your desired configuration. Refer to [this section](#configuration) for more details.

    > **_NOTE:_** Please pay special attention to the `http_proxy`, `https_proxy` and `additional_no_proxy` vars if you're behind proxy.

    For VM case:
    - update details relevant for vm_host (e.g.: datalane_interfaces, ...)
    - update VMs definition in host_vars/host-for-vms-1.yml - use that template for the first vm_host
    - update VMs definition in host_vars/host-for-vms-2.yml - use that template for the second and all other vm_hosts
    - update/create host_vars for all defined VMs (e.g.: host_vars/vm-ctrl-1.cluster1.local.yml and host_vars/vm-work-1.cluster1.local.yml)
      In case that vm_cluster_name is not defined or is empty, short host_vars file names should be used for VMs
      (e.g.: host_vars/vm-ctrl-1.yml and host_vars/vm-work-1.yml)
      Needed details are at least dataplane_interfaces
      For more details see [VM case configuration guide](docs/vm_config_guide.md)

10. **Mandatory:** Apply patch for Kubespray collection.

    ```bash
    ansible-playbook -i inventory.ini playbooks/k8s/patch_kubespray.yml
    ```

11. Execute `ansible-playbook`.

    > **_NOTE:_** It is recommended to use "--flush-cache" (e.g. "ansible-playbook -i --flush-cache inventory.ini playbooks/remote_fp.yml") when executing ansible-playbook in order to avoid unknown issues such as skip of tasks/roles, unable to update previous run inventory details, etc.
              
    ```bash
    ansible-playbook -i inventory.ini playbooks/${PROFILE}.yml
    ```

    > **_NOTE:_** For on_prem_aibox case, need to add "-b -K" flags for localhost deployment.
    ```bash
    ansible-playbook -i inventory.ini -b -K playbooks/on_prem_aibox.yml
    ```

    or, for VM case:

    ```bash
    ansible-playbook -i inventory.ini playbooks/vm.yml
    ```

    > **_NOTE:_** VMs are accessible from ansible host via ssh vm-ctrl-1 or ssh vm-work-1

## Cleanup

Refer to the [documentation](docs/redeploy_cleanup.md) to see details about how to cleanup existing deployment or specific feature.

## Configuration

Refer to the documentation linked below to see configuration details for selected capabilities and deployment profiles.

- [SRIOV Network Device Plugin and SRIOV CNI plugin](docs/sriov.md)
- [MinIO Operator](docs/storage.md)
- [Adding and removing worker node(s)](docs/add_remove_nodes.md)
- [VM case configuration guide](docs/vm_config_guide.md)
- [VM multinode setup guide](docs/vm_multinode_setup_guide.md)
- [VM cluster expansion guide](docs/vm_cluster_expansion_guide.md)
- [Non-root deployment guide](docs/rootless_deployment.md)

## Prerequisites and Requirements

- Required packages on the target servers: **Python3**.
- Required packages on the ansible host (where ansible playbooks are run): **Python3.8-3.10 and Pip3**.
- Required python packages on the ansible host.  **See requirements.txt**.

- SSH keys copied to all Kubernetes cluster nodes (`ssh-copy-id <user>@<host>` command can be used for that).
- For VM case SSH keys copied to all VM hosts (`ssh-copy-id <user>@<host>` command can be used for that).
- Internet access on all target servers is mandatory. Proxy is supported.
- At least 8GB of RAM on the target servers/VMs for minimal number of functions (some Docker image builds are memory-hungry and may cause OOM kills of Docker registry - observed with 4GB of RAM), more if you plan to run heavy workloads such as NFV applications.

- For the `RHEL`-like OSes `SELinux` must be configured prior to the CEK deployment and required `SELinux`-related packages should be installed.
  `CEK` itself is keeping initial `SELinux` state but `SELinux`-related packages might be installed during `k8s` cluster deployment as a dependency, for `Docker` engine e.g.,
  causing OS boot failure or other inconsistencies if `SELinux` is not configured properly.
  Preferable `SELinux` state is `permissive`.

  For more details, please, refer to the respective OS documentation.

## Contributing

Contributors, beside basic set of packages, should also install developer packages, using command:

```bash
pipenv install --dev
```

or

```bash
pip install -r ci-requirements.txt
```

### Run lint checks locally

Several lint checks are configured for the repository. All of them can be run on local environment using prepared bash scripts or by leveraging pre-commit hooks.

Prerequisite packages:

- developer python packages (ci-requirements.txt/Pipfile)
- shellcheck
- pre-commit python package

Required checks in CI:

- ansible-lint
- bandit
- pylint
- shellcheck

Check can be run by following command:

```bash
./scrits/run_<linter_name>.sh
```

or alternatively:

```bash
pre-commit run <linter_name> --all-files
```
