# Configuration Of Specific Features Using One Tag Deployment

It is also possible to deploy CEK with one tag execution in order to configure specific features, such as QAT, instead of running entire profile.

**Required:** Currently, CEK only support QAT and SGX configuration with one tag execution

                                                               QAT
**In the example below, QAT related roles such as grub settings, drivers, services, PFs / VFs bindings, Intel Device Plugin, etc., will be set up.**

```bash

ansible-playbook -i inventory.ini --flush-cache playbooks/full_nfv.yml --tags "intel-platform-qat-setup"

```

                                                               SGX
**In the example below, SGX related roles such as drivers, services, Intel Device Plugin, etc., will be set up.**

```bash

ansible-playbook -i inventory.ini --flush-cache playbooks/full_nfv.yml --tags "intel-platform-sgx-setup"

```

> Note: Update host_vars and group_vars as required, before using one tag deployment.
