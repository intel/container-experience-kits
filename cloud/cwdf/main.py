from .config import config_schema
from schema import SchemaError
import yaml
from jinja2 import Template
from os import path
import json


def verify_cwdf_config(config):
    # Verify config file has correct schema
    configuration = yaml.safe_load(config)
    try:
        pop = config_schema.validate(configuration)
        return pop
    except SchemaError as se:
        raise se


def compose_terraform(
        config, job_id, ssh_public_key,
        create_ansible_instance=True,
        create_container_registry=True):
    cwdf_configuration = verify_cwdf_config(config)
    aws_config = cwdf_configuration['awsConfig']

    extra_tags_json = json.dumps(aws_config["extra_tags"])
    aws_config["extra_tags_json"] = extra_tags_json.replace('"', '\\"')

    aws_config['job_id'] = job_id
    aws_config['ssh_pub_key'] = ssh_public_key

    aws_config["will_create_ansible_instance"] = create_ansible_instance
    aws_config["will_create_container_registry"] = create_container_registry

    tf_manifest = ""

    provider_template_path = path.join(
        path.dirname(__file__),
        'templates/terraform/aws/provider.tf.jinja')
    with open(provider_template_path, 'r') as f:
        provider_template = Template(f.read())
    tf_manifest += "### Provider ###\n"
    tf_manifest += provider_template.render(aws_config)
    tf_manifest += "### End of Provider ###\n\n"

    common_template_path = path.join(
        path.dirname(__file__),
        'templates/terraform/aws/common.tf.jinja')
    with open(common_template_path, 'r') as f:
        common_template = Template(f.read())
    tf_manifest += "### Common ###\n"
    tf_manifest += common_template.render(aws_config)
    tf_manifest += "### End of Common ###\n\n"

    if "instance_profiles" in aws_config:
        compute_template_path = path.join(
            path.dirname(__file__),
            'templates/terraform/aws/compute.tf.jinja')
        with open(compute_template_path, 'r') as f:
            compute_template = Template(f.read())
        tf_manifest += "### Bare Metal Compute ###\n"
        tf_manifest += compute_template.render(aws_config)
        tf_manifest += "### End of Bare Metal Compute ###\n\n"

    if "eks" in aws_config:
        eks_template_path = path.join(
            path.dirname(__file__),
            'templates/terraform/aws/eks.tf.jinja')
        with open(eks_template_path, 'r') as f:
            eks_template = Template(f.read())
        tf_manifest += "### Elastic Kubernetes Service ###\n"
        tf_manifest += eks_template.render(aws_config)
        tf_manifest += "### End of Elastic Kubernetes Service ###\n\n"

    if create_ansible_instance:
        ansible_host_template_path = path.join(
            path.dirname(__file__),
            'templates/terraform/aws/ansible_host.tf.jinja')
        with open(ansible_host_template_path, 'r') as f:
            ansible_host_template = Template(f.read())
        tf_manifest += "### Ansible Host ###\n"
        tf_manifest += ansible_host_template.render(aws_config)
        tf_manifest += "### End of Ansible Host ###\n\n"

    if create_container_registry:
        ecr_template_path = path.join(
            path.dirname(__file__),
            'templates/terraform/aws/ecr.tf.jinja')
        with open(ecr_template_path, 'r') as f:
            ecr_template = Template(f.read())
        tf_manifest += "### Elastic Container Registry ###\n"
        tf_manifest += ecr_template.render(aws_config)
        tf_manifest += "### End of Elastic Container Registry ###\n\n"

    return tf_manifest
