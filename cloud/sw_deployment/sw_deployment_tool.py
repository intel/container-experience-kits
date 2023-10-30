"""Script for deploying Reference Architecture (RA) on Cloud solutions"""
import os
import pathlib
import sys
import tarfile

import click
import jinja2
import yaml

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), os.pardir)))
from ssh_connector import SSHConnector, SSHHostKey  # pylint:disable=C0413,E0401
from docker_management import DockerManagement  # pylint:disable=C0413,E0401

configuration = {
    'cloud_settings': {
        'provider': None,
        'region': None
    },
    'ansible_host_ip': None,
    'ansible_ssh_host_key': None,
    'controller_ips': [],
    'worker_ips': [],
    'ssh_key': None,
    'ra_profile': None,
    'replicate_from_container_registry': None,
    'replicate_to_container_registry': None,
    'exec_containers': [],
    'custom_ami': None,
}

ROOT_DIR = pathlib.Path(__file__).absolute().parent.resolve()
DATA_DIR = os.path.join(ROOT_DIR, "data")
RA_DIR = pathlib.Path(ROOT_DIR).absolute().parents[1].resolve()

RA_REMOTE_PATH = os.path.join("/home/ubuntu", os.path.basename(RA_DIR))
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.ini")

TAR_NAME = "cloud_ra.tar.gz"
TAR_PATH = os.path.join("/tmp", TAR_NAME)

EKS_PATCH_NAME = "aws-node-ds-patch.yml"
EKS_PATCH_PATH = os.path.join(DATA_DIR, EKS_PATCH_NAME)

DISCOVERY_TOOL_PATH = "~/cwdf_deployment/discovery/discover.py"

DEFAULT_CONFIG = os.path.join(ROOT_DIR, '../deployment/sw.yaml')

nodes_list = []
node_host_keys = {}

@click.command()
@click.option('-c', '--config',
              type=click.Path(dir_okay=False),
              default=DEFAULT_CONFIG,
              help="Path to configuration file in yaml format.")
def main(config):
    """
    Main function for configuring whole cluster and deploy benchmark pods.

    Parameters:
    config (string): Path to configuration file for sw_deployment_tool

    Return:
    None

    """

    start_deploy(config=config)


def start_deploy(config):
    """
    Start deploying SW deployment.

    Parameters:
    config (string): Path to configuration file.

    Return:
    None

    """
    found_config = {}
    if os.path.exists(config):
        found_config = _parse_configuration_file(config)

    if not found_config:
        return

    found_config['ra_profile'] = _validate_ra_profile()

    _tar_repository(output_filename=TAR_PATH, source_dir=RA_DIR)
    _deploy(provider=found_config['cloud_settings']['provider'],
            ansible_host_ip=found_config['ansible_host_ip'],
            ssh_key=found_config['ssh_key'],
            ssh_user=found_config['ssh_user'],
            custom_ami=found_config['custom_ami'])


def _validate_ra_profile():
    group_vars_file = os.path.join(RA_DIR, "group_vars", "all.yml")
    if not pathlib.Path(group_vars_file).is_file():
        click.secho(f"ERROR - Configuration not found: {group_vars_file}", fg="red")
        exit()
    with open(file=group_vars_file, encoding="utf-8") as file:
        group_vars = yaml.safe_load(file)
        if group_vars.get('on_cloud') is None:
            click.secho("ERROR: on_cloud option not found", fg="red")
            exit()
        if not group_vars.get('on_cloud'):
            click.secho("ERROR: on_cloud set to false", fg="red")
            exit()
        return group_vars.get('profile_name')

def _tar_archive_filter(tarinfo):
    exclude = ['venv', '.terraform']
    if tarinfo.isdir() and any(substring in tarinfo.name for substring in exclude):
        return None
    else:
        return tarinfo

def _tar_repository(output_filename, source_dir):
    """
    Making tar.gz file that contains the RA repository.
    Creating a tar file is more convenient for submitting the
    repo to a cloud instance.

    Parameters:
    output_filename (string): Name of the tar.gz file
    source_dir (string): The path to the folder to be packed

    Return:
    None

    """
    if os.path.exists(output_filename):
        os.remove(output_filename)
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir), filter=_tar_archive_filter)


def _parse_configuration_file(config):
    """
    Get configuration from configuration.yaml
    If some of the parameters are set through cli,
    this settings have higher priority.

    Parameters:
    config (string): Path to the configuration file

    Return:
    dict:Configuration dictionary
    """
    if not os.path.exists(config):
        return None
    with open(config, 'r', encoding="UTF-8") as stream:
        try:
            file_configuration = yaml.safe_load(stream)
        except yaml.YAMLError as error:
            click.echo(error)
    if file_configuration is not None:
        for item in file_configuration:
            if file_configuration[item] is not None:
                configuration[item] = file_configuration[item]
    return configuration


def _remove_ssh_banner(ssh_client, node_ips_array, user):
    """
    Remove SSH for enabling root login via SSH.
    Using root is necessary for Ansible playbooks.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    node_ips_array (list): List of node IPs
    user (string): Regular remote user with enabled login

    Return:
    None

    """
    for node_ip in node_ips_array:
        ssh_client.exec_command(f"ssh-keyscan -H {node_ip} >> /home/ubuntu/.ssh/known_hosts")
        node_keyscan = ssh_client.exec_command(f"ssh-keyscan {node_ip}", return_parsed_output=True)
        node_keyscan = [line for line in node_keyscan.splitlines() if not line.startswith('#')]

        host_keys = []
        for node_key in node_keyscan:
            node_key = node_key.split()
            host_keys.append(SSHHostKey(node_key[1], node_key[2]))
        node_host_keys[node_ip] = host_keys

        if node_ip != "127.0.0.1":
            click.echo(f"{node_ip}, {user}")
            ssh_node = SSHConnector(ip_address=node_ip,
                                    username=user,
                                    port=22,
                                    host_keys=node_host_keys[node_ip],
                                    priv_key=configuration['ssh_key'],
                                    gateway=ssh_client.client)
            ssh_node.exec_command('sudo rm /root/.ssh/authorized_keys')
            ssh_node.exec_command(f"sudo cp /home/{user}/.ssh/authorized_keys /root/.ssh/")
            if configuration["cloud_settings"]["provider"] == "azure":
                ssh_node.exec_command("sudo sed -i '/^PermitRootLogin/s/no/yes/' /etc/ssh/sshd_config")
                ssh_node.exec_command("sudo sed -i 's/DenyUsers root omsagent nxautomation/DenyUsers omsagent nxautomation/g' /etc/ssh/sshd_config")
                ssh_node.exec_command("sudo systemctl restart sshd")
            ssh_node.close_connection()
        else:
            ssh_client.exec_command('sudo rm /root/.ssh/authorized_keys')
            ssh_client.exec_command(f"sudo cp /home/{user}/.ssh/authorized_keys /root/.ssh/")


def _install_dependencies_on_nodes(ssh_client, node_ips_array):
    """
    Installing lspci and golang as RA dependencies.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    node_ips_array (list): List of node IPs

    Return:
    None

    """
    for node_ip in node_ips_array:
        if node_ip != "127.0.0.1":
            ssh_node = SSHConnector(ip_address=node_ip,
                                    username="root",
                                    port=22,
                                    host_keys=node_host_keys[node_ip],
                                    priv_key=configuration['ssh_key'],
                                    gateway=ssh_client.client)
            ssh_node.exec_command(command='sudo apt-get update -y && sudo apt-get install -y pciutils golang',
                                  print_output=True)
            ssh_node.close_connection()
        else:
            ssh_client.exec_command(command='sudo apt-get update -y && sudo apt-get install -y pciutils golang',
                                    print_output=True)


def _discovery_nodes(ssh_client, root_user, node_ips, node_type):
    """
    Creating array with information of Ansible nodes.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    node_type (string): Ansible node type supported are: ['ra_host', 'ra_worker']

    Return:
    None

    """
    for node_ip in node_ips:
        ssh_client.exec_command(f"ssh-keyscan -H {node_ip} >> /home/ubuntu/.ssh/known_hosts")
        if node_ip != "127.0.0.1":
            ssh_node = SSHConnector(ip_address=node_ip,
                                    username=root_user,
                                    port=22,
                                    host_keys=node_host_keys[node_ip],
                                    priv_key=configuration['ssh_key'],
                                    gateway=ssh_client.client)
            node_hostname = ssh_node.exec_command(command='sudo cat /etc/hostname', return_parsed_output=True)
            ssh_node.close_connection()
        else:
            node_hostname = ssh_client.exec_command(command='sudo cat /etc/hostname', return_parsed_output=True)

        node = {
            "host_name": node_hostname,
            "internal_ip": node_ip,
            "root_user_name": root_user,
            "ansible_ssh_key_path": "/home/ubuntu/cwdf_deployment/ssh/id_rsa",
            "ansible_type": node_type
        }

        nodes_list.append(node)


def _create_inventory_file(ssh_client, nodes):
    """
    Creating inventory file for RA Ansible with information
    of all ansible nodes.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    nodes (list): List of node IPs

    Return:
    None

    """
    template_loader = jinja2.FileSystemLoader(searchpath=DATA_DIR)
    environment = jinja2.Environment(loader=template_loader, autoescape=True)
    template = environment.get_template("inventory.ini.j2")
    with open(INVENTORY_FILE, mode="w", encoding="utf-8") as inventory:
        inventory.write(template.render(hosts=nodes))

    ssh_client.copy_file(file_path=INVENTORY_FILE, destination_path=RA_REMOTE_PATH)
    os.remove(INVENTORY_FILE)


def _create_host_var_files(ssh_client, hosts):
    """
    Creating HostVar file for every cloud instance.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    hosts (list): List of host dictionaries created in _discovery_nodes function

    Return:
    None

    """
    for host in hosts:
        ssh_client.copy_file(file_path=os.path.join(RA_DIR, "host_vars", "node1.yml"),
                             destination_path=f"{RA_REMOTE_PATH}/host_vars/{host['host_name']}.yml")


def _docker_login(node_ips, ssh_client, user, registry, registry_username, password):
    """
    Login to private AWS ECR.

    Parameters:
    node_ips (list): List of K8s nodes
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    user (string): Host os username
    registry (string): URL address of private registry
    registry_username (string): Registry username
    password (string): Registry password

    Return:
    None

    """
    for node_ip in node_ips:
        ssh_host_key = SSHHostKey("ssh-rsa", configuration['ansible_ssh_host_key'])
        ssh_node = SSHConnector(node_ip, user, 22, [ssh_host_key], configuration['ssh_key'], ssh_client.client)
        ssh_node.exec_command(command=f"docker login {registry} --username {registry_username} --password {password}", print_output=True)
        ssh_node.close_connection()


def cleanup(config):
    """
    Cleanup function.

    Parameters:
    provider (string): Cloud provider ['aws', 'azure', 'gcp', 'ali', 'tencent']
    ansible_host_ip (string): The IP address of the instance where Ansible will run
    ssh_key (string): Path to private RSA key for autentification in Ansible instance

    Return:
    None

    """
    click.echo("-------------------")
    click.secho("Starting cleanup", fg="yellow")

    _parse_configuration_file(config=config)

    ssh_host_key = SSHHostKey("ssh-rsa", configuration['ansible_ssh_host_key'])
    client = SSHConnector(ip_address=configuration['ansible_host_ip'], username='ubuntu', host_keys=[ssh_host_key], priv_key=configuration['ssh_key'])

    for image in configuration['exec_containers']:
        image_name = image.replace('/', '-')
        click.echo(f"Deleting pod: {image_name}")
        client.exec_command(command=f"kubectl delete {image_name}", print_output=True)

    client.exec_command(f"cd {RA_REMOTE_PATH} && ansible-playbook -i inventory.ini ./playbooks/redeploy_cleanup.yml")
    client.exec_command(f"rm {RA_REMOTE_PATH} -rf")


def _deploy(provider, ansible_host_ip, ssh_key, ssh_user, custom_ami):
    """
    Function for deploy process of RA.

    Parameters:
    provider (string): Cloud provider ['aws', 'azure', 'gcp', 'ali', 'tencent']
    ansible_host_ip (string): The IP address of the instance where Ansible will run
    ssh_key (string): Path to private RSA key for autentification in Ansible instance
    custom_ami (string): Custom AMI to use for EKS cluster

    Return:
    None

    """
    click.echo("-------------------")
    click.secho(f"Connecting to Ansible instance with IP: {configuration['ansible_host_ip']}", fg="yellow")
    ssh_host_key = SSHHostKey("ssh-rsa", configuration['ansible_ssh_host_key'])
    client = SSHConnector(ip_address=ansible_host_ip, username='ubuntu', host_keys=[ssh_host_key], priv_key=ssh_key)

    click.echo("-------------------")
    click.secho("Copy private SSH key to Ansible instance", fg="yellow")
    client.copy_file(file_path=ssh_key, destination_path="/home/ubuntu/cwdf_deployment/ssh/id_rsa")

    client.exec_command("sudo chmod 600 /home/ubuntu/cwdf_deployment/ssh/id_rsa")

    click.echo("-------------------")
    click.secho("Copy RA repo as tar.gz file to Ansible instance", fg="yellow")
    client.copy_file(file_path=TAR_PATH, destination_path=f"/home/ubuntu/{TAR_NAME}")
    os.remove(TAR_PATH)

    click.echo("-------------------")
    click.secho("Extracting RA repo on Ansible instance", fg="yellow")
    client.exec_command(command=f"tar -zxf {TAR_NAME}", print_output=True)
    client.exec_command(f"rm /home/ubuntu/{TAR_NAME}")

    click.secho("\nEnabling root login", fg="yellow")
    _remove_ssh_banner(client, configuration['worker_ips'], ssh_user)
    _remove_ssh_banner(client, configuration['controller_ips'], 'ubuntu')

    click.secho("\nInstalling lspci on Ansible workers", fg="yellow")
    _install_dependencies_on_nodes(client, configuration['worker_ips'])
    _install_dependencies_on_nodes(client, configuration['controller_ips'])

    click.secho("\nDiscovering Ansible nodes", fg="yellow")
    _discovery_nodes(client, 'root', configuration['worker_ips'], "ra_worker")
    _discovery_nodes(client, 'root', configuration['controller_ips'], "ra_host")

    click.echo("-------------------")
    click.secho("Install cert-manager in EKS cluster", fg="yellow")
    commands = (
        "helm repo add jetstack https://charts.jetstack.io && "
        "helm repo update && "
        "helm install cert-manager jetstack/cert-manager "
        "--namespace cert-manager"
        "--create-namespace"
        "--version v1.10.0"
        "--set installCRDs=true"
    )

    client.exec_command(commands, print_output=True)

    click.echo("-------------------")
    click.secho("Install Multus in EKS cluster", fg="yellow")
    commands = """kubectl apply -f \
       https://raw.githubusercontent.com/k8snetworkplumbingwg/multus-cni/v4.0.2/deployments/multus-daemonset-thick.yml
       """

    client.exec_command(commands, print_output=True)

    if provider == 'aws':
        click.echo("-------------------")
        click.secho("Install Kubernetes Metrics Server", fg="yellow")
        commands = """kubectl apply -f \
        https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
        """

        client.exec_command(commands, print_output=True)

    if custom_ami == 'ubuntu':
        click.echo("-------------------")
        click.secho("Patch EKS cluster to support custom AMI", fg="yellow")
        client.copy_file(file_path=EKS_PATCH_PATH, destination_path=f"/tmp/{EKS_PATCH_NAME}")
        client.exec_command(f"kubectl patch ds aws-node -n kube-system --patch-file /tmp/{EKS_PATCH_NAME}")

    if provider == 'aws':
        registry_local_address = str(configuration['replicate_to_container_registry']).rsplit("/", maxsplit=1)[0]
        commands = (
            f'aws ecr get-login-password --region {configuration["cloud_settings"]["region"]} | '
            'REGISTRY_AUTH_FILE="/home/ubuntu/.crauth" '
            f'podman login -u AWS --password-stdin {registry_local_address}'
        )
    else:
        registry_local_address = str(configuration['replicate_to_container_registry'])
        commands = (
            f'az acr login --name {registry_local_address.split(".", maxsplit=1)[0]} --expose-token --output tsv --query accessToken | '
            'REGISTRY_AUTH_FILE="/home/ubuntu/.crauth" '
            'podman login -u 00000000-0000-0000-0000-000000000000 --password-stdin {registry_local_address}'
        )

    click.echo("-------------------")
    click.secho("Update container registry credentials", fg="yellow")
    client.exec_command(command=commands, print_output=True)

    click.echo("-------------------")
    click.secho("Creating inventory file", fg="yellow")
    _create_inventory_file(client, nodes_list)

    click.secho("\nInitializing RA repository", fg="yellow")
    commands = f"""cd {RA_REMOTE_PATH} && \
       python3 -m venv --copies --clear venv && \
       venv/bin/pip install -r requirements.txt && \
       venv/bin/ansible-galaxy install -r collections/requirements.yml
       """

    client.exec_command(command=commands, print_output=True)

    click.secho("\nCreating host_var files", fg="yellow")
    _create_host_var_files(client, nodes_list)

    commands = f"""cd {RA_REMOTE_PATH} && \
        venv/bin/ansible -i inventory.ini -m setup all > all_system_facts.txt
        """

    client.exec_command(command=commands)

    click.echo("-------------------")
    click.secho("Running RA Ansible playbooks", fg="yellow")
    click.secho("Selected profile:", fg="yellow")
    click.secho(configuration['ra_profile'], fg="green")

    ansible_playbook_commands = f"""cd {RA_REMOTE_PATH} && \
        venv/bin/ansible-playbook -i inventory.ini playbooks/k8s/patch_kubespray.yml
        venv/bin/ansible-playbook -i inventory.ini -e registry_local_address={registry_local_address} playbooks/{configuration['ra_profile']}.yml
    """
    client.exec_command(command=ansible_playbook_commands, print_output=True)

    click.echo("-------------------")
    click.secho("Remove private SSH key from Ansible instance", fg="yellow")
    client.exec_command("sudo rm /home/ubuntu/cwdf_deployment/ssh/id_rsa")

    client.close_connection()

    if (configuration['replicate_from_container_registry'] is not None and
            configuration['replicate_to_container_registry'] is not None and
            configuration['exec_containers']):
        click.echo("-------------------")
        click.secho("Copy Docker images to cloud registry")
        ssh_host_key = SSHHostKey("ssh-rsa", configuration['ansible_ssh_host_key'])
        ssh_client = SSHConnector(ip_address=ansible_host_ip, username='ubuntu', host_keys=[ssh_host_key], priv_key=ssh_key)
        click.echo(configuration['exec_containers'])
        click.echo(f"From registry: {configuration['replicate_from_container_registry']}")
        docker_mgmt = DockerManagement(from_registry=configuration['replicate_from_container_registry'],
                                       to_registry=configuration['replicate_to_container_registry'],
                                       images_to_replicate=configuration['exec_containers'],
                                       region=configuration['cloud_settings']['region'],
                                       cloud=provider,
                                       show_log=True)
        docker_mgmt.copy_images()

        _docker_login(node_ips=configuration['worker_ips'],
                      ssh_client=ssh_client,
                      user='root',
                      registry=configuration['replicate_to_container_registry'],
                      registry_username=docker_mgmt.cr_username,
                      password=docker_mgmt.cr_password)

        for image in configuration['exec_containers']:
            image_name = docker_mgmt.tagged_images[configuration['exec_containers'].index(image)]['repository']
            pod_name = docker_mgmt.tagged_images[configuration['exec_containers'].index(image)]['tag']
            click.echo(f"Starting pod: {pod_name}")
            ssh_client.exec_command(command=f"kubectl run {pod_name} --image={image_name} -n default", print_output=True)
        ssh_client.close_connection()


if __name__ == '__main__':
    # TODO get the config from... where?
    main(config=None)
