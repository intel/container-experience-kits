from .config import config_schema
from schema import SchemaError
import yaml
from jinja2 import Template
from os import path
import json
import urllib.request
import ipaddress
import click


aws_ubuntu_ami_ids = {
    "1.22": {
        "af-south-1": "ami-0abfddcc5c16f3827",
        "ap-east-1": "ami-0982b581ad077da7d",
        "ap-northeast-1": "ami-095ae6c226c7a0be8",
        "ap-northeast-2": "ami-05b503b4b512f6782",
        "ap-northeast-3": "ami-000e1ce14b5340e0d",
        "ap-south-1": "ami-06176107aa34fe3d2",
        "ap-southeast-1": "ami-03d3f0e32de10ef30",
        "ap-southeast-2": "ami-08613da851b7380d5",
        "ap-southeast-3": "ami-09bb527cbe16b7304",
        "ca-central-1": "ami-0fceb98a494c63260",
        "eu-central-1": "ami-0e5a8e4237d31a69d",
        "eu-north-1": "ami-0784242716a35096f",
        "eu-south-1": "ami-059e1846b88d7908f",
        "eu-west-1": "ami-0588693455f512664",
        "eu-west-2": "ami-04c81b7acfc75d46e",
        "eu-west-3": "ami-0ea60d5b7878386dd",
        "me-central-1": "ami-06fe9961383191226",
        "me-south-1": "ami-041c563c342ed66f8",
        "sa-east-1": "ami-010aa1bcf4256b7c5",
        "us-east-1": "ami-07d131ac12352754d",
        "us-east-2": "ami-0d203d2debcdee915",
        "us-west-1": "ami-044d771aa5148a486",
        "us-west-2": "ami-0f55debfeae4fc16e",
    },
    "1.23": {
        "af-south-1": "ami-0ba3e2009bda67497",
        "ap-east-1": "ami-0c1b479f821ca12d2",
        "ap-northeast-1": "ami-0bb53c7bc9bc1cdb2",
        "ap-northeast-2": "ami-0f7937a7c0d041aac",
        "ap-northeast-3": "ami-074ba39f795857ddb",
        "ap-south-1": "ami-04445fd4df5f54ee3",
        "ap-southeast-1": "ami-003ff41613f8c6804",
        "ap-southeast-2": "ami-0728197eb5f9eb69a",
        "ap-southeast-3": "ami-06c4cbce028720cef",
        "ca-central-1": "ami-0b6bb7a3526a235fb",
        "eu-central-1": "ami-0ad00cb0d1dd221b3",
        "eu-north-1": "ami-0605a17af3102f632",
        "eu-south-1": "ami-0132b02676f805d79",
        "eu-west-1": "ami-00d3a082b0bb86aa4",
        "eu-west-2": "ami-019444b54f257f28d",
        "eu-west-3": "ami-081fc1f5f1ff455dd",
        "me-central-1": "ami-0f0c688fadc38653d",
        "me-south-1": "ami-0628262209b372c90",
        "sa-east-1": "ami-0cb3dc8a5c6043e8d",
        "us-east-1": "ami-01c907a9b51818bd9",
        "us-east-2": "ami-0f72983b275d18583",
        "us-west-1": "ami-09bfff2dabea6d722",
        "us-west-2": "ami-0880011c56a3540d5",
    }
}

def verify_cwdf_config(config):
    # Verify config file has correct schema
    configuration = yaml.safe_load(config)
    try:
        pop = config_schema.validate(configuration)
        cloud_provider = pop["cloudProvider"]

        # Check if user has whitelisted current external IP
        external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')
        ip_addr = ipaddress.ip_address(external_ip)
        cidr_blocks = pop[f'{cloud_provider}Config']['sg_whitelist_cidr_blocks']
        whitelisted = False
        for block in cidr_blocks:
            ip_net = ipaddress.ip_network(block)
            if ip_addr in ip_net:
                whitelisted = True
                break
        if not whitelisted:
            pop[f'{cloud_provider}Config']['sg_whitelist_cidr_blocks'].append(external_ip + "/32")
            click.echo(f'Whitelisted your current external IP address {external_ip}.')
        return pop
    except SchemaError as se:
        raise se


def compose_terraform(
        config, job_id, ssh_public_key,
        create_ansible_instance=True,
        create_container_registry=True):
    cwdf_configuration = verify_cwdf_config(config)

    cloud_provider = cwdf_configuration["cloudProvider"]

    if cloud_provider == "aws":
        cloud_config = cwdf_configuration["awsConfig"]
    elif cloud_provider == "azure":
        cloud_config = cwdf_configuration["azureConfig"]
    else:
        return

    extra_tags_json = json.dumps(cloud_config["extra_tags"])
    cloud_config["extra_tags_json"] = extra_tags_json.replace('"', '\\"')

    cloud_config['job_id'] = job_id
    cloud_config['ssh_pub_key'] = ssh_public_key

    cloud_config["will_create_ansible_instance"] = create_ansible_instance
    cloud_config["will_create_container_registry"] = create_container_registry

    tf_manifest = ""

    provider_template_path = path.join(
        path.dirname(__file__),
        f'templates/terraform/{cloud_provider}/provider.tf.jinja')
    with open(provider_template_path, 'r') as f:
        provider_template = Template(f.read())
    tf_manifest += "### Provider ###\n"
    tf_manifest += provider_template.render(cloud_config)
    tf_manifest += "### End of Provider ###\n\n"

    common_template_path = path.join(
        path.dirname(__file__),
        f'templates/terraform/{cloud_provider}/common.tf.jinja')
    with open(common_template_path, 'r') as f:
        common_template = Template(f.read())
    tf_manifest += "### Common ###\n"
    tf_manifest += common_template.render(cloud_config)
    tf_manifest += "### End of Common ###\n\n"

    if cloud_provider == "aws":
        if "instance_profiles" in cloud_config:
            compute_template_path = path.join(
                path.dirname(__file__),
                'templates/terraform/aws/compute.tf.jinja')
            with open(compute_template_path, 'r') as f:
                compute_template = Template(f.read())
            tf_manifest += "### Bare Metal Compute ###\n"
            tf_manifest += compute_template.render(cloud_config)
            tf_manifest += "### End of Bare Metal Compute ###\n\n"

        if "eks" in cloud_config:
            version = cloud_config["eks"]["kubernetes_version"]
            region = cloud_config["region"]
            ami_id = aws_ubuntu_ami_ids[version][region]
            cloud_config["eks_ubuntu_ami_id"] = ami_id
            eks_template_path = path.join(
                path.dirname(__file__),
                'templates/terraform/aws/eks.tf.jinja')
            with open(eks_template_path, 'r') as f:
                eks_template = Template(f.read())
            tf_manifest += "### Elastic Kubernetes Service ###\n"
            tf_manifest += eks_template.render(cloud_config)
            tf_manifest += "### End of Elastic Kubernetes Service ###\n\n"
    elif cloud_provider == "azure":
        if "aks" in cloud_config:
            aks_template_path = path.join(
                path.dirname(__file__),
                'templates/terraform/azure/aks.tf.jinja')
            with open(aks_template_path, 'r') as f:
                compute_template = Template(f.read())
            tf_manifest += "### Azure Kubernetes Service ###\n"
            tf_manifest += compute_template.render(cloud_config)
            tf_manifest += "### End of Azure Kubernetes Service ###\n\n"

    if create_ansible_instance:
        ansible_host_template_path = path.join(
            path.dirname(__file__),
            f'templates/terraform/{cloud_provider}/ansible_host.tf.jinja')
        with open(ansible_host_template_path, 'r') as f:
            ansible_host_template = Template(f.read())
        tf_manifest += "### Ansible Host ###\n"
        tf_manifest += ansible_host_template.render(cloud_config)
        tf_manifest += "### End of Ansible Host ###\n\n"

    if create_container_registry:
        cr_template_path = path.join(
            path.dirname(__file__),
            f'templates/terraform/{cloud_provider}/cr.tf.jinja')
        with open(cr_template_path, 'r') as f:
            cr_template = Template(f.read())
        tf_manifest += "### Managed Container Registry ###\n"
        tf_manifest += cr_template.render(cloud_config)
        tf_manifest += "### End of Managed Container Registry ###\n\n"

    return tf_manifest, cwdf_configuration
