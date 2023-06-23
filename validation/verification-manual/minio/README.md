# Check MinIO Operator/Console and Tenant
The Storage Configuration Profile deploys the MinIO operator/console and sample MinIO tenant via Helm charts. You can verify that the MinIO operator/console and the tenant are present on the system. As MinIO with distributed mode, it requires more than four nodes and one controller. 
```
# kubectl get pods -n minio-operator
NAME                             READY   STATUS    RESTARTS   AGE
console-6c9557b87d-zzmgt         1/1     Running   0          12m
minio-operator-7885bb8d4-9l2sq   1/1     Running   0          12m
minio-operator-7885bb8d4-k4j8m   1/1     Running   0          12m
minio-operator-7885bb8d4-lcm56   1/1     Running   0          12m
minio-operator-7885bb8d4-xh5vp   1/1     Running   0          12m
```
```
# kubectl get pods -n minio-tenant
NAME                  READY   STATUS    RESTARTS   AGE
minio-tenant-ss-0-0   1/1     Running   0          12m
minio-tenant-ss-0-1   1/1     Running   0          12m
minio-tenant-ss-0-2   1/1     Running   0          12m
minio-tenant-ss-0-3   1/1     Running   0          12m
```

After the sample MinIO tenant is deployed successfully on four nodes, it requires four volumes per server. You must confirm that all volumes are properly bound.
```
# kubectl get pv
NAME                         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                                    STORAGECLASS      REASON   AGE
…
mnt-data-1-am09-19-cyp       1Gi        RWO            Retain           Bound    minio-tenant/data1-minio-tenant-ss-0-0   local-storage              19m
mnt-data-1-am09-22-cyp       1Gi        RWO            Retain           Bound    minio-tenant/data2-minio-tenant-ss-0-3   local-storage              19m
mnt-data-1-am09-24-cyp       1Gi        RWO            Retain           Bound    minio-tenant/data0-minio-tenant-ss-0-1   local-storage              19m
mnt-data-1-am09-26-cyp       1Gi        RWO            Retain           Bound    minio-tenant/data0-minio-tenant-ss-0-2   local-storage              19m
…
```
```
kubectl get pvc -n minio-tenant
NAME                        STATUS   VOLUME                   CAPACITY   ACCESS MODES   STORAGECLASS    AGE
…
data0-minio-tenant-ss-0-0   Bound    mnt-data-2-am09-19-cyp   1Gi        RWO            local-storage   20m
data1-minio-tenant-ss-0-0   Bound    mnt-data-1-am09-19-cyp   1Gi        RWO            local-storage   20m
data2-minio-tenant-ss-0-0   Bound    mnt-data-4-am09-19-cyp   1Gi        RWO            local-storage   20m
data3-minio-tenant-ss-0-0   Bound    mnt-data-3-am09-19-cyp   1Gi        RWO            local-storage   20m
…
```

