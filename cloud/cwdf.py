import click
from cwdf import compose_terraform
import os
from Crypto.PublicKey import RSA


@click.group()
def cli():
    pass


def generate_ssh_keys(ssh_dir, public_key_path, private_key_path):
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir)
        private_key = RSA.generate(2048)
        with open(private_key_path, 'wb') as f:
            f.write(private_key.exportKey('PEM'))
        public_key = private_key.publickey()
        with open(public_key_path, 'wb') as f:
            f.write(public_key.exportKey('OpenSSH'))
        os.chmod(private_key_path, 0o600)


@click.command()
@click.option('--cwdf_config', help='Path to CWDF yaml config file', required=True)
@click.option('--ssh_public_key', help='Path to SSH public key', required=False)
@click.option('--generate_keys', help='Should generate SSH key automatically', default=False)
@click.option('--job_id', help='Unique identifier that will be included in resource tags and names', default="manual")
@click.option('--create_ansible_host', help='Will include ansible host in the Terraform manifest', default=True)
@click.option('--create_container_registry', help='Will include managed container registry in the Terraform manifest', default=True)
def generate_terraform(cwdf_config, ssh_public_key, generate_keys, job_id, create_ansible_host, create_container_registry):
    with open(cwdf_config, 'r') as f:
        cwdf_config = f.read()

    if ssh_public_key is None or generate_keys is True:
        ssh_dir = os.path.join(os.getcwd(), "ssh")
        public_key_path = os.path.join(ssh_dir, "id_rsa.pub")
        private_key_path = os.path.join(ssh_dir, "id_rsa")
        generate_ssh_keys(ssh_dir, public_key_path, private_key_path)
        with open(public_key_path, 'r') as f:
            ssh_public_key = f.read()
    else:
        with open(ssh_public_key, 'r') as f:
            ssh_public_key = f.read().strip()

    tf_manifest = compose_terraform(cwdf_config, job_id, ssh_public_key, create_ansible_host, create_container_registry)
    click.echo(tf_manifest)


cli.add_command(generate_terraform)


if __name__ == "__main__":
    cli()
