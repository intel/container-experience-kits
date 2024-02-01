# Cleanup mechanism
1. [Introduction](#introduction)
2. [Run cleanup playbook](#Run-cleanup-playbook)
3. [Run cleanup playbook for specific role/tag](#Run-cleanup-playbook-for-specific-role/tag)

## Introduction
With cleanup mechanism user can use the redeploy_cleanup playbook to cleanup deployed k8s cluster and prepare for redeploy. User should be able to use tags to cleanup specific features.

Cleanup mechanism should clean existing deployment, but there is no guarantee to get system OS to the same state as before deployment.

Deploying different profile after cleanup is not supported. 

Re-run of the same profile without cleanup is supported, but without significant changes to configuration in host/group vars.

Cleanup of specific features is currently not supported.

## Run cleanup playbook
```bash
    ansible-playbook -i inventory.ini playbooks/redeploy_cleanup.yml
```

## Run cleanup playbook for specific tag - in future
```bash
    ansible-playbook -i inventory.ini playbooks/redeploy_cleanup.yml --tags "your_tag"
```
