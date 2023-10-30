import ipaddress
import json
import os
import shutil
import stat

import click
import requests
import yaml

from jinja2 import Template, Environment, FileSystemLoader

from .config import config_schema


def click_secho_error(message, bold=True):
    click.secho(message, err=True, bold=bold, fg='red')


def verify_cwdf_config(config):
    # Verify config file has correct schema
    configuration = yaml.safe_load(config)
    pop = config_schema.validate(configuration)
    cloud_provider = pop["cloudProvider"]

    # Check if user has whitelisted current external IP
    req = requests.get('https://ident.me', timeout=600)
    if req.status_code != 200:
        click_secho_error("The server https://ident.me is not responding properly.")
        click_secho_error("Unable to find your IP address.", bold=False)
        return

    external_ip = req.text
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


def compose_cloudcli(
        deployment_dir, config, job_id, public_key_path,
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

    cloud_config.update({
        'job_id': job_id,
        'ssh_pub_key_path': public_key_path,
        "will_create_ansible_instance": create_ansible_instance,
        "will_create_container_registry": create_container_registry,
    })

    with open(public_key_path, 'r') as f:
        cloud_config["ssh_public_key"] = f.read()

    provider_template_path = os.path.join(
        os.path.dirname(__file__),
        f'templates/cloudcli/{cloud_provider}/')

    if cloud_provider == "aws":
        # version = cloud_config["eks"]["kubernetes_version"]
        # region = cloud_config["region"]
        file_loader = FileSystemLoader(provider_template_path)
        env = Environment(loader=file_loader, autoescape=True)
        shutil.copy2(os.path.join(provider_template_path, 'aws_cloudcli_cleanup.sh'), deployment_dir)
        cleanup_file = os.path.join(deployment_dir, 'aws_cloudcli_cleanup.sh')
        print(f"Cleanup file path: {cleanup_file}")
        st = os.stat(cleanup_file)
        os.chmod(cleanup_file, st.st_mode | stat.S_IEXEC)
        script_template = env.get_template("aws_cloudcli_deploy.sh.j2")
    elif cloud_provider == "azure":
        file_loader = FileSystemLoader(provider_template_path)
        env = Environment(loader=file_loader, autoescape=True)
        shutil.copy2(os.path.join(provider_template_path, 'azure_cloudcli_cleanup.sh'), deployment_dir)
        cleanup_file = os.path.join(deployment_dir, 'azure_cloudcli_cleanup.sh')
        st = os.stat(cleanup_file)
        os.chmod(cleanup_file, st.st_mode | stat.S_IEXEC)
        script_template = env.get_template("azure_cloudcli_deploy.sh.j2")
    else:
        click_secho_error(f"Unknown cloud provider {cloud_provider}.")
        click_secho_error("Currently supported cloud providers are: aws, azure, gpc.")
        click_secho_error("Nothing to do.")
        return

    generated_script = script_template.render(cloud_config=cloud_config)
    script_file = os.path.join(deployment_dir, f"{cloud_provider}_cloudcli_provisioning.sh")

    with open(file=script_file, mode='wt', encoding='UTF-8') as sf:
        sf.write(generated_script)

    return script_file


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

    provider_template_path = os.path.join(
        os.path.dirname(__file__),
        f'templates/terraform/{cloud_provider}/provider.tf.jinja')
    with open(provider_template_path, 'r') as file:
        provider_template = Template(file.read())
    tf_manifest += "### Provider ###\n"
    tf_manifest += provider_template.render(cloud_config)
    tf_manifest += "### End of Provider ###\n\n"

    common_template_path = os.path.join(
        os.path.dirname(__file__),
        f'templates/terraform/{cloud_provider}/common.tf.jinja')
    with open(common_template_path, 'r') as file:
        common_template = Template(file.read())
    tf_manifest += "### Common ###\n"
    tf_manifest += common_template.render(cloud_config)
    tf_manifest += "### End of Common ###\n\n"

    if cloud_provider == "aws":
        if "instance_profiles" in cloud_config:
            compute_template_path = os.path.join(
                os.path.dirname(__file__),
                'templates/terraform/aws/compute.tf.jinja')
            with open(compute_template_path, 'r') as file:
                compute_template = Template(file.read())
            tf_manifest += "### Bare Metal Compute ###\n"
            tf_manifest += compute_template.render(cloud_config)
            tf_manifest += "### End of Bare Metal Compute ###\n\n"

        if "eks" in cloud_config:
            eks_template_path = os.path.join(
                os.path.dirname(__file__),
                'templates/terraform/aws/eks.tf.jinja')
            with open(eks_template_path, 'r') as file:
                eks_template = Template(file.read())
            tf_manifest += "### Elastic Kubernetes Service ###\n"
            tf_manifest += eks_template.render(cloud_config)
            tf_manifest += "### End of Elastic Kubernetes Service ###\n\n"
    elif cloud_provider == "azure":
        if "aks" in cloud_config:
            aks_template_path = os.path.join(
                os.path.dirname(__file__),
                'templates/terraform/azure/aks.tf.jinja')
            with open(aks_template_path, 'r') as file:
                compute_template = Template(file.read())
            tf_manifest += "### Azure Kubernetes Service ###\n"
            tf_manifest += compute_template.render(cloud_config)
            tf_manifest += "### End of Azure Kubernetes Service ###\n\n"

    if create_ansible_instance:
        ansible_host_template_path = os.path.join(
            os.path.dirname(__file__),
            f'templates/terraform/{cloud_provider}/ansible_host.tf.jinja')
        with open(ansible_host_template_path, 'r') as file:
            ansible_host_template = Template(file.read())
        tf_manifest += "### Ansible Host ###\n"
        tf_manifest += ansible_host_template.render(cloud_config)
        tf_manifest += "### End of Ansible Host ###\n\n"

    if create_container_registry:
        cr_template_path = os.path.join(
            os.path.dirname(__file__),
            f'templates/terraform/{cloud_provider}/cr.tf.jinja')
        with open(cr_template_path, 'r') as file:
            cr_template = Template(file.read())
        tf_manifest += "### Managed Container Registry ###\n"
        tf_manifest += cr_template.render(cloud_config)
        tf_manifest += "### End of Managed Container Registry ###\n\n"

    return tf_manifest, cwdf_configuration
