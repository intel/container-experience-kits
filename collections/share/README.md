# Ansible Collection - cek.share


# Motivation
This Ansible Collection is to share CEK roles or modules to other consumer who just wants to use part of CEK. You can use one of below ways to import CEK collection to your Ansible environemnt, then add its role folder to your ansible role path.
* Import it by direct cmdline
    ```
     $ ansible-galaxy collection install git+https://github.com/intel/container-experience-kits.git#/collections/share -p ./
     or
     $ ansible-galaxy collection install git+https://github.com/intel/container-experience-kits.git#/collections/share,{branch_or_tag} -p ./
    ```
* Import it by requirements file
    Edit a requirements.yml file like below :
    ```
    collections:
    - source: https://github.com/intel/container-experience-kits.git#/collections/share
        type: git
    ```
    or 

    ```
    collections:
    - source: https://github.com/intel/container-experience-kits.git#/collections/share
        type: git
        version: {branch_or_tag}
    ```
    
    Then import it by below shell script :
    ```
        #!/bin/bash
        export ANSIBLE_COLLECTIONS_PATH=$PWD;
        ansible-galaxy collection install -r requirements.yml
    ```
# Supported Roles and Modules
Currently, below roles are shared in this collection :
* ## configure_dpdk <br>

    User can set condition and variable values to execute different task blocks in this role :
    - Set "dyna_config_dpdk_bind" to true, the role task block will bind dpdk with E810 NIC devices, generate /etc/network_env.conf, and add a systemd service to rebind after reboot.
    - Set "dyna_config_dpdk_link" to true, set "dpdk_link_node1" and "dpdk_link_node2" to the two servers which have E810 NIC linked with 100Gbps cable. The role task block will update /etc/network_env.conf to exchange src/dst mac addresses.
    - Set "dyna_config_dpdk_unbind" to true, the role task will recover system to status before calling bind.
    Below is an example for how CEK playbook uses this role:
    ```
    # bind and unbind operation no limit to node count
    - hosts: "{{node | default('kube_node')}}"
      roles:
      - role: configure_dpdk
        tags:
          - dyna_config_dpdk
        when:
          - dyna_config_dpdk_bind | default(false) | bool or
            dyna_config_dpdk_unbind | default(false) | bool

    # link operation only can work on two nodes
    - hosts: "{{node | default('kube_node')}}"
      roles:
        - role: configure_dpdk
          dpdk_link_node1: "{{ groups.kube_node[0] }}"
          dpdk_link_node2: "{{ groups.kube_node[1] }}"
          dpdk_link_pre: true
          tags:
            - dyna_config_dpdk
          when:
            - dyna_config_dpdk_link | default(false) | bool

    - hosts: localhost
      roles:
        - role: configure_dpdk
          dpdk_link_node1: "{{ groups.kube_node[0] }}"
          dpdk_link_node2: "{{ groups.kube_node[1] }}"
          tags:
            - dyna_config_dpdk
          when:
            - dyna_config_dpdk_link | default(false) | bool

    - hosts: "{{node | default('kube_node')}}"
      roles:
        - role: configure_dpdk
          dpdk_link_node1: "{{ groups.kube_node[0] }}"
          dpdk_link_node2: "{{ groups.kube_node[1] }}"
          dpdk_link_post: true
          tags:
            - dyna_config_dpdk
          when:
            - dyna_config_dpdk_link | default(false) | bool
    ```
    Below is another example for how CEK playbook uses this role in system cleanup
    ```
    - name: cleanup dyna config dpdk
      include_role:
        name: configure_dpdk
        tasks_from: cleanup
      tags:
        - dyna_config_dpdk
    ```

* ## install_gpu_driver <br>
    User can use this role to install Intel GPU software stack, including :
    * kernel mode driver : 
        * i915
        * firmwares
    * User mode driver and runtimes
        * Graphics: OpenGL, OpenGL ES, Vulkan
        * Media: VAAPI, VPL, MSDK
        * Compute: OpenCL, Level Zero 
    * Tools :
        * vainfo
        * glxinfo
        * clinfo
        * vulkaninfo
        * intel_gpu_top
        * xpu-smi
    Below is a example to use this role.

    ```
     - role: install_gpu_driver     
    ```
    
