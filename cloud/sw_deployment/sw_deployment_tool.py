"""Script for deploying Reference Architecture (RA) on Cloud solutions"""
import os
import tarfile
import shutil
import click
import yaml
import jinja2
import pathlib
import sys
from ssh_connector import SSHConnector
from git_clone import clone_repository, switch_repository_to_tag
from docker_management import DockerManagement

configuration = {
    'cloud_settings': {
        'provider': None,
        'region': None
    },
    'ansible_host_ip': None,
    'controller_ips': [],
    'worker_ips': [],
    'ssh_key': None,
    'git_url': None,
    'git_tag': None,
    'github_personal_token': None,
    'git_branch': None,
    'ra_config_file': None,
    'ra_profile': None,
    'ra_machine_architecture': None,
    'ra_ignore_assert_errors': None,
    'replicate_from_container_registry': None,
    'replicate_to_container_registry': None,
    'exec_containers': [],
    'skip_git_clonning': True
}

ROOT_DIR = pathlib.Path(__file__).absolute().parent.resolve()
DATA_DIR = os.path.join(ROOT_DIR, "data")
RA_CLONED_REPO = os.path.join(DATA_DIR,
                              "container-experience-kits")
RA_REMOTE_PATH = "/home/ubuntu/container-experience-kits"
INVENTORY_FILE=os.path.join(DATA_DIR, "inventory.ini")

TAR_NAME = "git_repo.tar.gz"
TAR_PATH = os.path.join(DATA_DIR, TAR_NAME)

DISCOVERY_TOOL_PATH = "~/cwdf_deployment/discovery/discover.py"

DEFAULT_CONFIG=os.path.join(ROOT_DIR, '../deployment/sw.yaml')

nodes_list = []

@click.command()
@click.option('-p','--provider',
              type=click.Choice(['aws', 'azure', 'gcp', 'ali', 'tencent']),
              help='Select cloud provider where RA will be deploy. [aws, azure, gcp, alibaba, tencent])')
@click.option('--ansible-host-ip', help='IP address of instance where Ansible will be running')
@click.option('--controller-ips', help='Array of K8s controller IPs')
@click.option('--worker-ips', help='Array of K8s worker IPs')
@click.option('--ssh-key', help='SSH key for accessing the cloud instances')
@click.option('--git-url', help='The URL address of the Git project that will be cloned into the Cloud instance')
@click.option('--ra-config-file', help='Configuration file with')
@click.option('--ra-profile',
              type=click.Choice(['access', 'basic', 'full_nfv', 'on_prem', 'regional_dc', 'remote_fp', 'storage', 'build_your_own']),
              help='Selection of RA profile. At the moment, '
                   'Container Experience Kits supports the following profiles: '
                   'access, basic, full_nfv, on_prem, regional_dc, remote_fp, '
                   'storage, build_your_own')
@click.option('--ra-machine-architecture',
              type=click.Choice(['spr', 'icx', 'clx', 'skl']),
              help='CPU architecture of cloud instance. Supported architectures are: '
                   'spr - Sapphire Rapids - 4th Generation Intel(R) Xeon(R) Scalable Processor'
                   'icx - IceLake (default) - 3rd Generation Intel(R) Xeon(R) Scalable Processor'
                   'clx - CascadeLake - 2nd Generation Intel(R) Xeon(R) Scalable Processor'
                   'skl - SkyLake - 1st Generation Intel(R) Xeon(R) Scalable Processor')
@click.option('--github-personal-token', help='Git token with permission to clone selected repository')
@click.option('--git-tag', help='Clone Git repository with specified tag')
@click.option('--git-branch', default='master', help='Clone Git repository with specified branch')
@click.option('--ra-ignore-assert-errors', default=False, help='Ignore assert errors in RA deployment')
@click.option('-c', '--config',
              type=click.Path(dir_okay=False),
              default=DEFAULT_CONFIG,
              help="Path to configuration file in yaml format.")
@click.option('--skip-git-clonning', is_flag=True, default=True, help='Skip clonning repository from Git and use already clonned directory.')
@click.option('--replicate-from-container-registry', help='URL address of source docker registry')
@click.option('--replicate-to-container-registry', help='URL address of target docker registry')
@click.option('--exec-containers', multiple=True, help='List of containers to be executed')
def main(provider, ansible_host_ip, controller_ips,
         worker_ips, ssh_key, git_url, ra_config_file,
         ra_profile, ra_machine_architecture, github_personal_token,
         git_tag, git_branch, ra_ignore_assert_errors, config,
         skip_git_clonning, replicate_from_container_registry,
         replicate_to_container_registry, exec_containers):
    """
    Main function for configuring whole cluster and deploy benchmark pods.

    Parameters:
    provider (string): Cloud provider where RA will be deploy. [aws, azure, gcp, alibaba, tencent]
    ansible_host_ip (string): IP address of Ansible host
    controller_ips (list): List of Ansible controller instances
    worker_ips (list): List of Ansible worker instances
    ssh_key (string): Path to private SSH key
    git_url (string): URL of Git repository to be clonned to Ansible instance
    ra_config_file (string): Path to configuration file for RA
    ra_profile (string): Selection of RA profile
    ra_machine_architecture (string): CPU architecture of cloud instance
    github_personal_token (string): Personal GitHub token for clonning private repositories
    git_tag (string): To clone Git repository with specified tag
    git_branch (string): Clone Git repository with specified branch
    ra_ignore_assert_errors (bool): Ignore assert errors in RA deployment
    config (string): Path to configuration file for sw_deployment_tool
    skip_git_clonning (bool): Skip clonning repository from Git and use already clonned directory
    replicate_from_container_registry (string): URL address of source docker registry
    replicate_to_container_registry (string): URL address of target docker registry
    exec_containers (list): List of containers to be executed

    Return:
    None

    """
    arguments = locals()
    for argument in arguments:
        if arguments[argument] is not None:
            configuration[argument] = arguments[argument]

    start_deploy(config=config)

    

def start_deploy(config):
    """
    Start deploying SW deployment.

    Parameters:
    config (string): Path to configuration file.

    Return:
    None

    """
    if os.path.exists(config):
        configuration = _parse_configuration_file(config)
    if configuration['skip_git_clonning']:
        if os.path.exists(RA_CLONED_REPO):
            shutil.rmtree(RA_CLONED_REPO)
        repository = clone_repository(clone_dir=RA_CLONED_REPO,
                                    repo_url=configuration['git_url'],
                                    token=configuration['github_personal_token'],
                                    branch=configuration['git_branch'])

        if configuration['git_tag'] is not None:
            switch_repository_to_tag(repo=repository, tag=configuration['git_tag'])

    _tar_repository(output_filename=TAR_PATH, source_dir=RA_CLONED_REPO)

    _deploy(provider=configuration['cloud_settings']['provider'],
           ansible_host_ip=configuration['ansible_host_ip'],
           ssh_key=configuration['ssh_key'])


def _tar_repository(output_filename, source_dir):
    '''
    Making tar.gz file that contains clonned repository.
    Creating a tar file is more convenient for submitting a
    cloned repository to a cloud instance.

    Parameters:
    output_filename (string): Name of the tar.gz file
    source_dir (string): The path to the folder to be packed

    Return:
    None

    '''
    if os.path.exists(output_filename):
        os.remove(output_filename)
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

def _parse_configuration_file(config):
    '''
    Get configuration from configuration.yaml
    If some of the parameters are set through cli,
    this settings have higher priority.

    Parameters:
    config (string): Path to the configuration file

    Return:
    dict:Configuration dictionary

    '''
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
    '''
    Remove SSH for enabling root login via SSH.
    Using root is necessary for Ansible playbooks.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    node_ips_array (list): List of node IPs
    user (string): Regular remote user with enabled login

    Return:
    None

    '''
    for node_ip in node_ips_array:
        ssh_client.exec_command(f"ssh-keyscan -H {node_ip} >> /home/ubuntu/.ssh/known_hosts")
        if node_ip != "127.0.0.1":
            click.echo(f"{node_ip}, {user}")
            ssh_node = SSHConnector(node_ip, user, 22, configuration['ssh_key'], ssh_client.client)
            ssh_node.exec_command('sudo rm /root/.ssh/authorized_keys')
            ssh_node.exec_command(f"sudo cp /home/{user}/.ssh/authorized_keys /root/.ssh/")
            ssh_node.close_connection()
        else:
            ssh_client.exec_command('sudo rm /root/.ssh/authorized_keys')
            ssh_client.exec_command(f"sudo cp /home/{user}/.ssh/authorized_keys /root/.ssh/")

def _install_dependencies_on_nodes(ssh_client, node_ips_array):
    '''
    Installing lspci and golang as RA dependencies.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    node_ips_array (list): List of node IPs

    Return:
    None

    '''
    for node_ip in node_ips_array:
        if node_ip != "127.0.0.1":
            ssh_node = SSHConnector(ip_address=node_ip,
                                    username="root",
                                    port=22,
                                    priv_key=configuration['ssh_key'],
                                    gateway=ssh_client.client)
            ssh_node.exec_command('yum makecache && yum -y install pciutils.x86_64 golang',
                                  print_output=True)
            ssh_node.close_connection()
        else:
            ssh_client.exec_command('yum makecache && yum -y install pciutils.x86_64 golang',
                                    print_output=True)

def _discovery_nodes(ssh_client, root_user, node_ips, node_type):
    '''
    Creating array with information of Ansible nodes.

    Parameters:
    ssh_client (SSHConnector obj): SSHConnector object with active connection
    node_type (string): Ansible node type supported are: ['ra_host', 'ra_worker']

    Return:
    None

    '''
    for node_ip in node_ips:
        ssh_client.exec_command(f"ssh-keyscan -H {node_ip} >> /home/ubuntu/.ssh/known_hosts")
        if node_ip != "127.0.0.1":
            ssh_node = SSHConnector(node_ip, root_user, 22, configuration['ssh_key'], ssh_client.client)
            node_hostname = ssh_node.exec_command('sudo cat /etc/hostname')
            ssh_node.close_connection()
        else:
            node_hostname = ssh_client.exec_command('sudo cat /etc/hostname')

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
    environment = jinja2.Environment(loader=template_loader)
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
        if host['internal_ip'] != '127.0.0.1':
            ssh_worker = SSHConnector(ip_address=host['internal_ip'],
                                      username=host['root_user_name'],
                                      port=22,
                                      priv_key=configuration['ssh_key'],
                                      gateway=ssh_client.client)
            ethernet_devices = ssh_worker.exec_command("lspci | grep 'ther' | awk '{print $1}", )
            ssh_worker.close_connection()
        else:
            ethernet_devices = ssh_client.exec_command("lspci | grep 'ther' | awk '{print $1}", )

        with open(file=os.path.join(DATA_DIR, "node1.yml"), encoding="utf-8") as file:
            list_doc = yaml.safe_load(file)

        list_doc["profile_name"] = configuration['ra_profile']
        list_doc["configured_arch"] = configuration['ra_machine_architecture']

        dataplane_interfaces = []

        for address in ethernet_devices.split('\n'):
            dataplane_interface = {
                'bus_info': address,
                'default_vf_driver': 'ena',
                'name': 'eth0',
                'pf_driver': 'ena',
                'sriov_numvfs': 6,
                'sriov_vfs': {
                    'vf_00': 'vfio-pci',
                    'vf_05': 'vfio-pci'
                    }}
            dataplane_interfaces.append(dataplane_interface)

        list_doc["dataplane_interfaces"] =  dataplane_interfaces

        if configuration['ra_profile'] == "access":
            list_doc = _set_access_profile(list_doc)
        if configuration['ra_profile'] == "basic":
            list_doc = _set_basic_profile(list_doc)
        if configuration['ra_profile'] == "full_nfv":
            list_doc = _set_full_nfv_profile(list_doc)
        if configuration['ra_profile'] == "on_prem":
            list_doc = _set_on_prem_profile(list_doc)
        if configuration['ra_profile'] == "regional_dc":
            list_doc = _set_regional_dc_profile(list_doc)
        if configuration['ra_profile'] == "remote_fp":
            list_doc = _set_remote_fp_profile(list_doc)
        if configuration['ra_profile'] == "storage":
            list_doc = _set_storage_profile(list_doc)

        with open(file=os.path.join(DATA_DIR, f"{host['host_name']}.yml"),
                  mode="w",
                  encoding="utf-8") as file:
            yaml.dump(list_doc, file)

        ssh_client.copy_file(file_path=os.path.join(DATA_DIR, f"{host['host_name']}.yml"),
                             destination_path=f"{RA_REMOTE_PATH}/host_vars/{host['host_name']}.yml")
        os.remove(os.path.join(DATA_DIR, f"{host['host_name']}.yml"))

def _set_access_profile(settings):
    """
    Function for additional settings for RA access profile.

    Parameters:
    settings (list): List of dictionaries contains settings of RA profile

    Return:
    list:List of dictionaries contains settings of RA profile

    """
    return settings

def _set_regional_dc_profile(settings):
    """
    Function for additional settings for RA regional dc profile.

    Parameters:
    settings (list): List of dictionaries contains settings of RA profile

    Return:
    list:List of dictionaries contains settings of RA profile

    """
    additional_settings = {
        "configure_gpu": False,
        "gpu_dp_enabled": False
    }
    settings.update(additional_settings)
    return settings

def _set_basic_profile(settings):
    """
    Function for additional settings for RA basic profile.

    Parameters:
    settings (list): List of dictionaries contains settings of RA profile

    Return:
    list:List of dictionaries contains settings of RA profile

    """
    additional_settings = {
    }
    settings.update(additional_settings)
    return settings

def _set_full_nfv_profile(settings):
    """
    Function for additional settings for RA Full NFV profile.

    Parameters:
    settings (list): List of dictionaries contains settings of RA profile

    Return:
    list:List of dictionaries contains settings of RA profile

    """
    additional_settings = {
    }
    settings.update(additional_settings)
    return settings

def _set_on_prem_profile(settings):
    """
    Function for additional settings for RA On prem profile.

    Parameters:
    settings (list): List of dictionaries contains settings of RA profile

    Return:
    list:List of dictionaries contains settings of RA profile

    """
    additional_settings = {
        "update_qat_drivers": False
    }
    settings.update(additional_settings)
    return settings

def _set_remote_fp_profile(settings):
    """
    Function for additional settings for RA remote fp profile.

    Parameters:
    settings (list): List of dictionaries contains settings of RA profile

    Return:
    list:List of dictionaries contains settings of RA profile

    """
    additional_settings = {
    }
    settings.update(additional_settings)
    return settings

def _set_storage_profile(settings):
    """
    Function for additional settings for RA storage profile.

    Parameters:
    settings (list): List of dictionaries contains settings of RA profile

    Return:
    list:List of dictionaries contains settings of RA profile

    """
    additional_settings = {
    }
    settings.update(additional_settings)
    return settings

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
        ssh_node = SSHConnector(node_ip, user, 22, configuration['ssh_key'], ssh_client.client)
        ssh_node.exec_command(f"docker login {registry} --username {registry_username} --password {password}", print_output=True)
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

    client = SSHConnector(ip_address=configuration['ansible_host_ip'], username='ubuntu', priv_key=configuration['ssh_key'])

    for image in configuration['exec_containers']:
        image_name = image.replace('/','-')
        click.echo(f"Deleting pod: {image_name}")
        client.exec_command(f"kubectl delete {image_name}", print_output=True)

    client.exec_command(f"cd {RA_REMOTE_PATH} && ansible-playbook -i inventory.ini ./playbooks/redeploy_cleanup.yml")
    client.exec_command(f"rm {RA_REMOTE_PATH} -rf")

def _deploy(provider, ansible_host_ip, ssh_key):
    """
    Function for deploy process of RA.

    Parameters:
    provider (string): Cloud provider ['aws', 'azure', 'gcp', 'ali', 'tencent']
    ansible_host_ip (string): The IP address of the instance where Ansible will run
    ssh_key (string): Path to private RSA key for autentification in Ansible instance

    Return:
    None

    """
    click.echo("-------------------")
    click.secho(f"Connecting to Ansible instance with IP: {configuration['ansible_host_ip']}", fg="yellow")
    client = None
    if provider == 'aws':
        client = SSHConnector(ip_address=ansible_host_ip, username='ubuntu', priv_key=ssh_key)

    click.echo("-------------------")
    click.secho("Copy private SSH key to Ansible instance", fg="yellow")
    client.copy_file(file_path=ssh_key, destination_path=f"/home/ubuntu/cwdf_deployment/ssh/id_rsa")

    client.exec_command(f"sudo chmod 600 /home/ubuntu/cwdf_deployment/ssh/id_rsa")

    click.echo("-------------------")
    click.secho("Copy clonned git repo as tar.gz file to Ansible instance", fg="yellow")
    client.copy_file(file_path=TAR_PATH, destination_path=f"/home/ubuntu/{TAR_NAME}")
    os.remove(TAR_PATH)

    client.exec_command(f"tar -xvf {TAR_NAME}", print_output=False)
    client.exec_command(f"rm /home/ubuntu/{TAR_NAME}")

    click.secho("\nEnabling root login", fg="yellow")
    _remove_ssh_banner(client, configuration['worker_ips'], 'ec2-user')
    _remove_ssh_banner(client, configuration['controller_ips'], 'ubuntu')

    click.secho("\nInstalling lspci on Ansible workers", fg="yellow")
    _install_dependencies_on_nodes(client, configuration['worker_ips'])
    _install_dependencies_on_nodes(client, configuration['controller_ips'])

    click.secho("\nDiscovering Ansible nodes", fg="yellow")
    _discovery_nodes(client, 'root', configuration['worker_ips'], "ra_worker")
    _discovery_nodes(client, 'root', configuration['controller_ips'], "ra_host")

    click.echo("-------------------")
    click.secho("Creating invenotry file", fg="yellow")
    _create_inventory_file(client, nodes_list)

    click.secho("\nInitializing RA repository", fg="yellow")
    commands = f"""cd {RA_REMOTE_PATH} && \
       git submodule update --init && \
       sudo python3 -m pip install -r requirements.txt && \
       export PROFILE={configuration['ra_profile']} && \
       make k8s-profile PROFILE={configuration['ra_profile']} ARCH={configuration['ra_machine_architecture']}
       """

    client.exec_command(commands, print_output=True)

    click.secho("\nCreating host_var files", fg="yellow")
    _create_host_var_files(client, nodes_list)

    client.exec_command(f"{RA_REMOTE_PATH}/ansible -i inventory.ini -m setup all > {RA_REMOTE_PATH}/all_system_facts.txt")

    click.echo("-------------------")
    click.secho("Running RA Ansible playbooks", fg="yellow")
    click.secho("Selected profile:", fg="yellow")
    click.secho(configuration['ra_profile'], fg="green")

    ansible_playbook_commnads = f"""
        ansible-playbook -i {RA_REMOTE_PATH}/inventory.ini {RA_REMOTE_PATH}/playbooks/intel/{configuration['ra_profile']}.yml && \
        ansible-playbook -i {RA_REMOTE_PATH}/inventory.ini {RA_REMOTE_PATH}/playbooks/k8s/post_deployment_hooks.yml
    """
    client.exec_command(command=ansible_playbook_commnads, print_output=True)
    client.close_connection()

    if (configuration['replicate_from_container_registry'] is not None and 
        configuration['replicate_to_container_registry'] is not None and 
        configuration['exec_containers'] is not None):
        click.echo("-------------------")
        click.secho("Copy Docker images to cloud registry")
        if provider == 'aws':
            ssh_client = SSHConnector(ip_address=ansible_host_ip, username='ubuntu', priv_key=ssh_key)
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
                      registry_username=docker_mgmt.ECR_USERNAME,
                      password=docker_mgmt.ECR_PASSWORD)

        for image in configuration['exec_containers']:
            image_name = docker_mgmt.tagged_images[configuration['exec_containers'].index(image)]['repository']
            pod_name = docker_mgmt.tagged_images[configuration['exec_containers'].index(image)]['tag']
            click.echo(f"Starting pod: {pod_name}")
            ssh_client.exec_command(f"kubectl run {pod_name} --image={image_name} -n default", print_output=True)
        ssh_client.close_connection()

if __name__ == '__main__':
    main()
