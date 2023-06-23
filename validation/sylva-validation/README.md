# Stack and CNF Validation

## Summary

Scripts for testing environment to validate if Telco Cloud Kubernetes features were activated and available to pods, and to validate that CNFs are getting those Kubernetes features allocated. These scripts were not designed and hardened to run in end user environment. BMRA verify based on access profile. 

## Stack Validation

Test cases check for:

* Component level architecture specifications of [Anuket Reference Architecture Kubernetes Component Level Architecture specifications](https://github.com/anuket-project/anuket-specifications/blob/master/doc/ref_arch/kubernetes/chapters/chapter04.rst)

* Device Plugins SRIOV DPDK, and Multus CNI

More in folder [stack-validation](./stack-validation/).

## CNF Validation

Test case checks CNF allocation of SR-IOV devices like VFs or accelerators.

More in folder [cnf-validation](./cnf-validation/).

