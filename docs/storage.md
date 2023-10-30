# Local Static Volume Provisioner
## Cluster Configurations
To use the local static volume provisioner, you need to set the `local_volume_provisioner_enabled ` to `true` in the group_vars/all.yml file. Then you can customerize your storage class name per your workload by setting `local_volume_provisioner_storage_class`, and if no change, the default value is local-static-storage.

## Disk configuration
Then you need to configure the disk information for storage in the host_vars/\<nodename\>.yml based your systemd disk information.
```
persistent_volumes: []
#persistent_volumes:
#  - name: "mnt-data-1"                         # PV identifier will be used for PVs names followed by node name(e.g., mnt-data-1-hostname)
#    mountPath: /mnt/disks/disk0                # Mount path of a volume, for local provisioner, it musts match /mnt/disks/* pattern
#    device: /dev/nvme0n1                       # Target storage device name when creating a volume. Only set it when storage_deploy_test_mode is false
#    fsType: ext4                               # file system types, by default is ext4.

```
If you do not have real disks inserted into your machine, and you still want to try the k8s provisioner, you can just enable `storage_deployment_test_mode` in the group_vars/all.yml. RA will automitically create 6 10GiB fake loop devices for simulation and fill the persistent_volumes automatically inside.

## Simple Verification
After the deployment successfully, you can claim a persistent-volume-claim for verification w/ below commd:
```
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: user-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: local-static-storage
```

# Rook-Ceph Operator
## Operator Configuration
To use the rook-ceph operator as your k8s storage framework. You need to set the `rook_ceph.enabled` to `true` in the group_vars/all.yml file. Same as local volume static provisioner, you can customerize your `storage_class` name, otherwise, the default value is `rook-cephfs`. Also, you can choose the storage method for your workload/solution, by default the backend uses `cephfs` as default storage method.
```
rook_ceph:
  enabled: true
  storage_class: "rook-cephfs"    # Storage class name
  storage_type: "cephfs"          # Storage type for rook-ceph, supported values[cephfs, block, object]  
```
## Disk Configuration
Same as described in local volume static provisioner.

# MinIO Operator/Console/Tenant

## Cluster configuration options

In order to install MinIO Operator/Console set `minio_enabled` value to `true` in your group vars file. Setting it to `false` will disable Minio Operator/Console installation and cause other related options to be ignored.
```yaml
minio_enabled: true
```

In order to install MinIO Tenant sample set `minio_tenant_enabled` value to `true` in your group vars file. Setting it to `false` won't install Minio Tenant sample and cause other related options(host vars) to be ignored.
```yaml
minio_tenant_enabled: true
```

You can also change the MinIO Operator/Console namespace used for the MinIO Operator/Console deployment - by default it's `minio-operator`.
```yaml
minio_operator_namespace: minio-operator
```

You can also change the MinIO Tenant namespace used for the MinIO Tenant sample deployment - by default it's `minio-tenant`.
```yaml
minio_tenant_namespace: minio-tenant
```
### Access to MinIO Console

From your controller, get the JWT (Jason Web Token) to the MinIO Console Access
```bash
kubectl get secret $(kubectl get serviceaccount console-sa --namespace minio-operator -o jsonpath="{.secrets[0].name}") --namespace minio-operator -o jsonpath="{.data.token}" | base64 --decode
```

Now you will need to forward the port of MinIO Console service.
```bash
kubectl --namespace minio-operator port-forward svc/console 9090:9090
```

Depending on your environment, you can use tunnel to access your console. Here, I used the remote tunnel on x.x.x.x which I can open the MinIO Console UI
```bash
ssh -R 9090:localhost:9090 user_id@x.x.x.x
```

You can now open the browser on your laptop, and use the generated JWT to access Console UI at `localhost:9090`.


## Worker node specific options

There's also a set of configuration options that are applied in per-node manner.

First set of variables enable Persistent Volumes and also this info was used for sample tenant deployment. You would need your own tenant settings.
```yaml
persistent_volumes:
  - name: "mnt-data-1"                         # PV identifier will be used for PVs names followed by node name(e.g., mnt-data-1-hostname)
    storageClassName: "local-storage"          # Storage class name to match with PVC
    accessMode: "ReadWriteOnce"                # Access mode when mounting a volume, e.g., ReadWriteOnce/ReadOnlyMany/ReadWriteMany/ReadWriteOncePod
    persistentVolumeReclaimPolicy: "Retain"    # Reclaim policy when a volume is released once it's bound, e.g., Retain/Recycle/Delete
    mountPath: /mnt/disks/disk0                # Mount path of a volume, for local provisioner, it musts match /mnt/disks/* pattern
    device: /dev/nvme0n1                       # Target storage device name when creating a volume. Only set it when storage_deploy_test_mode is false
    fsType: ext4                               # file system types
```

## Sample Tenants
In order to deploy the sample tenants, 4 or more worker nodes would be ideal for distributed mode. Current sample tenant deployment has two different modes. 

1. Test Mode (`minio_deploy_test_mode: true`)
In an automation environment, this mode is useful and deployed on a special block device called the loop device when no extra storage device, which maps a normal file onto a virtual block device. This allows for the file to be used as a **virtual file system** inside another file. 

2. Distributed Mode (`minio_deploy_test_mode: false`)
In clustering environment, this mode provides object storage service to build high performance infrastructure for machine learning, analytics and application data workloads. This mode uses local storage devices like hard disk, m.2 ssd, etc.

### Sample Tenant Secret Key
A MinIO user is an identity that includes at minimum credentials consisting of an Access Key and Secret Key. MinIO requires all incoming requests include credentials which match an existing user. You can find default credentials in 
```yaml
secrets:
  # create a kubernetes secret object with the accessKey and secretKey as defined here.
  enabled: true
  name: minio1-secret
  accessKey: minio
  secretKey: minio123
```
in ./role/minio_install/templates/minio_tenant_custom_values.yml.j2
 
Please refer to the [MinIO Operator](https://github.com/minio/operator) to get more details and usage examples.
