# Cloud RA

## Prerequisites

- Python 3.8+
- AWS CLI 2+
- Terraform 1.2+
- Docker 20.10.17+
- `pip install -r requirements.txt`
- `aws configure`

## Managed Kubernetes deployment

### Automatic

Create deployment directory with `cwdf.yaml`, `sw.yaml` hardware and software configuration files:

```commandline
mkdir deployment
vim cwdf.yaml
vim sw.yaml
```

Example `cwdf.yaml` file:
```yaml
cloudProvider: aws
awsConfig:
  profile: default
  region: eu-central-1
  vpc_cidr_block: "10.21.0.0/16"
  # These tags will be applied to all created resources
  extra_tags:
    Owner: "some_user"
    Project: "CWDF"
  subnets:
    - name: "subnet_a"
      az: eu-central-1a
      cidr_block: "10.21.1.0/24"
    - name: "subnet_b"
      az: eu-central-1b
      cidr_block: "10.21.2.0/24"
  sg_whitelist_cidr_blocks:
    - "0.0.0.0/0"
  eks:
    kubernetes_version: "1.22"
    # AWS EKS requires at least 2 subnets
    subnets: ["subnet_a", "subnet_b"]
    node_groups:
      - name: "default"
        instance_type: "t3.medium"
        vm_count: 3
```

Then `sw.yaml` for the software configuration.
[Link to sw_deployment tool README file.](sw_deployment/README.md)

Example `sw.yaml` file:
```yaml
cloud_settings:
  provider: aws
  region: eu-central-1
controller_ips:
- 127.0.0.1
# exec_containers can be used to deploy additional containers or workloads.
# It defaults to an empty list, but can be changed as shown in the commented lines
exec_containers: []
#exec_containers:
#- ubuntu/kafka
git_tag: None
git_url: https://github.com/intel/container-experience-kits
github_personal_token: None
ra_config_file: data/node1.yaml
ra_ignore_assert_errors: true
ra_machine_architecture: skl
ra_profile: build_your_own
replicate_from_container_registry: https://registry.hub.docker.com
```

Then run `deployer.py deploy` and pass the deployment directory as an argument:
```commandline
python deployer.py deploy --deployment_dir=deployment
```

Along with the EKS cluster additional Ansible instance and ECR container registry will be created.

Ansible instance will be available with AWS CLI, Ansible and kubectl pre-installed.
Kubectl will be also pre-configured and authorized against created EKS cluster.
On the Ansible instance default user is `ubuntu`. Folder `cwdf_deployment` in home directory contains ssh keys for EKS worker nodes and connection info for worker nodes and ECR registry.

After the deployment discovery will run on each EKS worker node. Output will be written to `discovery_results` directory on local machine where `deployer.py` is running and then copied to Ansible host's `cwdf_deployment` directory.

Cleanup created resources:
```commandline
python deployer.py cleanup --deployment_dir=deployment
```

### Manual

Start by creating a directory for the deployment and generate SSH key for instances:
```commandline
mkdir deployment
mkdir deployment/ssh
ssh-keygen -f deployment/ssh
```

1. Create a `cwdf` hardware definition yaml file e.g. `cwdf.yaml`:
```commandline
cp cwdf_example.yaml deployment/cwdf.yaml
```

2. Then generate Terraform manifest using `cwdf.py`:
```commandline
python cwdf.py generate-terraform \
  --cwdf_config=deployment/cwdf.yaml \
  --ssh_public_key=deployment/ssh/id_rsa.pub \
  --job_id=manual \
  --create_ansible_host=True \
  --create_container_registry=True \
  > deployment/main.tf
```

3. Initialize Terraform and deploy resources in the deployment directory:
```commandline
terraform init
terraform apply
```
