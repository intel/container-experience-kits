# Policy Controller

The `policy-controller` admission controller can be used to enforce policy on a Kubernetes cluster based on verifiable supply-chain metadata from `cosign`.

`policy-controller` also resolves the image tags to ensure the image being ran is not different from when it was admitted.

See the [installation instructions](https://docs.sigstore.dev/policy-controller/installation) for more information.

Today, `policy-controller` can automatically validate signatures and
attestations on container images.
Enforcement is configured on a per-namespace basis, and multiple keys are supported.

We're actively working on more features here.

For more information about the `policy-controller`, have a look at our documentation website [here](https://docs.sigstore.dev/policy-controller/overview).

## Examples

Please see the [examples/](./examples/) directory for example policies etc.

## Policy Testing

This repo includes a `policy-tester` tool which enables checking a policy against
various images.

In the root of this repo, run the following to build:
```
make policy-tester
```

Then run it pointing to a YAML file containing a ClusterImagePolicy, and an image to evaluate the policy against:
```
(set -o pipefail && \
    ./policy-tester \
        --policy=test/testdata/policy-controller/tester/cip-public-keyless.yaml \
        --image=ghcr.io/sigstore/cosign/cosign:v1.9.0 | jq)
```

## Support Policy

This policy-controller's versions are able to run in the following versions of Kubernetes:

|  | policy-controller `> 0.2.x` |
|---|:---:|
| Kubernetes 1.22 | ✓ |
| Kubernetes 1.23 | ✓ |
| Kubernetes 1.24 | ✓ |
| Kubernetes 1.25 | ✓ |
| Kubernetes 1.26 | ✓ |

note: not fully tested yet, but can be installed

## Release Cadence

We are intending to move to a monthly cadence for minor releases.
Minor releases will be published around the beginning of the month.
We may cut a patch release instead, if the changes are small enough not to warrant a minor release.
We will also cut patch releases periodically as needed to address bugs.

## Security

Should you discover any security issues, please refer to sigstores [security
process](https://github.com/sigstore/community/blob/main/SECURITY.md)


###########################################################################################################


## Additional info added by RA integration

## Enable policy-controller feature before deploy RA

Edit group_vars/all.yml to make sure sigstore_policy_controller_install: true

After BMRA deployed, do below container image signing tests:

## Private/Public Key based policy

Below is an example to sign an image:
```
docker pull nginx:latest
docker tag nginx:latest <k8s ctl hostname>:30500/key/nginx-signed:latest
docker push <k8s ctl hostname>:30500/key/nginx-signed:latest
cosign sign --key k8s://my-cosign-namespace/cosign-key <k8s ctl hostname>:30500/key/nginx-signed:latest
```
Let's push a unsigned image to compare
```
docker tag nginx:latest <k8s ctl hostname>:30500/key/nginx-unsigned:latest
docker push <k8s ctl hostname>:30500/key/nginx-unsigned:latest
```

## Successful case when image was signed correctly

Deploy the signed image:
```
kubectl apply -f -  << EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pubkey
  namespace: my-cosign-namespace
spec:
 containers:
 - name: nginx
   image: <k8s ctl hostname>:30500/key/nginx-signed:latest
   imagePullPolicy: Always
 imagePullSecrets:
   - name: container-registry-secret
EOF
```
It will say:
pod/signed-pubkey created

## Failed case when image is not signed

Deploy the unsigned image:
```
kubectl apply -f -  << EOF
apiVersion: v1
kind: Pod
metadata:
  name: nginx-unsigned
  namespace: my-cosign-namespace
spec:
 containers:
 - name: nginx
   image: <k8s ctl hostname>:30500/key/nginx-unsigned:latest
   imagePullPolicy: Always
 imagePullSecrets:
   - name: container-registry-secret
EOF
```
It will say:
Error from server (BadRequest): admission webhook "policy.sigstore.dev" denied the request: validation failed: failed policy: ra-test-image-policy-pub-key: spec.containers[0].image
ra-test:30500/key/nginx-unsigned@sha256:942ae2dfd73088b54d7151a3c3fd5af038a51c50029bfcfd21f1e650d9579967 signature
keyless validation failed for authority authority-0 for ra-test:30500/key/nginx-unsigned@sha256:942ae2dfd73088b54d7151a3c3fd5af038a51c50029bfcfd21f1e650d9579967: no matching signatures:

## Keyless based policy
We use an external container registry for example, but you can also use k8s local registry.

```
kubectl apply -f -  << EOF
apiVersion: policy.sigstore.dev/v1alpha1
kind: ClusterImagePolicy
metadata:
  name: ghcr-io-image-policy-keyless
spec:
  images:
    - glob: ghcr.io/alekdu/**
  authorities:
  - keyless:
      url: https://fulcio.sigstore.dev
      identities:
        - issuerRegExp: https://github.com/login/oauth
          subjectRegExp: alek.du@intel.com
EOF
```
## Successful case when image was signed correctly
```
kubectl run signed-nginx --image=ghcr.io/alekdu/nginx-keyless-signed:latest --namespace my-cosign-namespace
```

It will say:
pod/signed-nginx created

## Failed case when image is not signed
```
kubectl run signed-nginx --image=ghcr.io/alekdu/nginx-keyless-unsigned:latest --namespace my-cosign-namespace
```

It will say:
Error from server (BadRequest): admission webhook "policy.sigstore.dev" denied the request: validation failed: failed policy: ghcr-io-image-policy-keyless: spec.containers[0].image
ghcr.io/alekdu/nginx-keyless-unsigned@sha256:942ae2dfd73088b54d7151a3c3fd5af038a51c50029bfcfd21f1e650d9579967 signature
keyless validation failed for authority authority-0 for ghcr.io/alekdu/nginx-keyless-unsigned@sha256:942ae2dfd73088b54d7151a3c3fd5af038a51c50029bfcfd21f1e650d9579967: no matching signatures:
