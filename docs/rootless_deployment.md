# Running deployment as non root user
PREREQUISITES:

Existing non root user on all machines, where it is requested.
E.g.: ansible host, target host(s) for BMRA/VMRA deployment.
Existing non root user needs to have password set and on target host(s) needs to be added into sudo group (with passwordless access)

Example how to add user on:
UBUNTU FAMILY:
```
useradd -m -d /home/$USER -s /bin/bash $USER
usermod -aG sudo $USER
passwd $USER
```

RHEL FAMILY:
```
useradd -m -d /home/$USER -s /bin/bash $USER
usermod -aG wheel $USER
passwd $USER
visudo (update secure_path to `secure_path = /sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin` due to PATH update for rootless user)
```

Inventory file inventory.ini have to be edited (in the root project dir). Following parameters are relevant:
- ansible_user to be set to $USER (default "root")
- ansible_password to be set to $USER's password if needed.
- ansible_become_pass to be set to $USER's sudo/become password. This can be set for each host.

```
[all]
host-1 ansible_host=10.10.0.5 ip=10.10.0.5 ansible_user=test_user ansible_password=test ansible_become_pass=test
```

**_NOTE:_** If we want to use commandline option '-K' to ask for non root user sudo password at the beginning of deployment then
all non root users have to use the same sudo password ! It will require the same sudo password even for non root user on ansible host.
For this case is expected that there is the same non root user created on all ansible and target machines.


## To start deployment as non root user just run following commands with --become flag
### On BMRA

```
ansible-playbook -i inventory.ini playbooks/${PROFILE}.yml --become

or

ansible-playbook -i inventory.ini playbooks/${PROFILE}.yml --become -K
and then type $USER sudo password
```

### On VMRA

```
ansible-playbook -i inventory.ini playbooks/vm.yml --become

or

ansible-playbook -i inventory.ini playbooks/vm.yml --become -K
and then type $USER sudo password
```
