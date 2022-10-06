<!--
  Copyright (c) 2020-2022 Intel Corporation.

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->
# MinIO ![license](https://img.shields.io/badge/license-AGPL%20V3-blue)

[MinIO](https://min.io) is a High Performance Object Storage released under GNU AGPLv3 or later. It is API compatible
with Amazon S3 cloud storage service. Use MinIO to build high performance infrastructure for machine learning, analytics
and application data workloads.

For more detailed documentation please visit [here](https://docs.minio.io/)

Introduction
------------

This chart bootstraps MinIO Tenant on a [Kubernetes](http://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

Configure MinIO Helm repo
--------------------

```bash
helm repo add minio https://operator.min.io/
```

Creating a Tenant with Helm Chart
-----------------

Once the [MinIO Operator Chart](https://github.com/minio/operator/tree/master/helm/operator) is successfully installed, create a MinIO Tenant using:

```bash
helm install --namespace tenant-ns \
  --create-namespace tenant minio/tenant
```

This creates a 4 Node MinIO Tenant (cluster). To change the default values, take a look at various [values.yaml](https://github.com/minio/operator/blob/master/helm/tenant/values.yaml).
