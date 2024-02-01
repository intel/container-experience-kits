# Run VMs on cluster using KubeVirt kubernetes add-on

Following instructions can be used to test provision of VMs on Kubernetes cluster using KubeVirt

More information can be found at official documentation of KubeVirt:

- KubeVirt Usage - <https://kubevirt.io/labs/kubernetes/lab1>
- KubeVirt Architecture - <https://kubevirt.io/user-guide/architecture/>
- KubeVirt Configuration - <https://kubevirt.io/user-guide/operations/installation/>

## Test instructions

Test resource yaml can be found at [vm.yaml](vm.yaml).

1. Apply resource vm.yaml to get Virtual machine created:

    ```bash
    $ kubectl create namespace vm-test
    namespace/vm-test created

    $ kubectl apply -n vm-test -f vm.yaml
    virtualmachine.kubevirt.io/testvm created
    ```

2. Check VM has been created:

    ```bash
    $ kubectl get vms -n vm-test
    NAME     AGE   STATUS    READY
    testvm   21s   Stopped   False
    ```

3. Start created VM

    ```bash
    $ virtctl start testvm -n vm-test
    VM testvm was scheduled to start
    ```

4. Check status of VM instance to be `running`:

    ```bash
    $ kubectl get vmis -n vm-test
    NAME     AGE   PHASE     IP              NODENAME      READY
    testvm   20s   Running   10.244.88.198   ad07-07-cyp   True
    ```

5. Access VM's console:

    ```bash
    $ virtctl console -n vm-test testvm
    Successfully connected to testvm console. The escape sequence is ^]

    ```
    __Note:__ Hit enter to get login page and login with the displayed username and password. You can disconnect from the virtual machine console by typing: `ctrl+]`.

6. Stop & Delete VM:

    ```bash
    $ virtctl stop testvm -n vm-test
    VM testvm was scheduled to stop
    
    $ kubectl delete vm testvm -n vm-test
    virtualmachine.kubevirt.io "testvm" deleted

    $ kubectl delete namespace vm-test
    namespace "vm-test" deleted
    ```
