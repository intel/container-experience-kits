# SW Deployment part

In this folder is example configuration file (sw_deployment/configure.yaml).

Example of configure.yaml file:
```yaml
ansible_host_ip: xxx.xxx.xxx.xxx
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
git_url: https://<token>@github.com/intel/container-experience-kits
github_personal_token: xxxxxxxxxxxxxxxxxxx
ra_config_file: data/node1.yaml
ra_ignore_assert_errors: true
ra_machine_architecture: skl
ra_profile: build_your_own
replicate_from_container_registry: https://registry.hub.docker.com
replicate_to_container_registry: <ecr url>
ssh_key: ../deployment/ssh/id_rsa
worker_ips:
- xxx.xxx.xxx.xxx
- xxx.xxx.xxx.xxx
- xxx.xxx.xxx.xxx
```

For proper functionality, modify `github_personal_token` with a personal GitHub token with access to the RA repository.
To deploy to a different cloud region, adjust the `region` setting using the target region.

The following list of settings will be adjusted automatically:
- `ansible_host_ip`
- `worker_ips`
- `replicate_to_container_registry`

After whole deployment the list of containers are deployed. Place the selected containers in the `exec_containers` list.
Furthermore, it is necessary to set the source repository in the `replicate_from_container_registry` setting.
