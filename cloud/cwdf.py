import click
from cwdf import compose_terraform


@click.group()
def cli():
    pass


@click.command()
@click.option('--cwdf_config', help='Path to CWDF yaml config file', required=True)
@click.option('--ssh_public_key', help='Path to SSH public key', required=True)
@click.option('--job_id', help='Unique identifier that will be included in resource tags and names', default="manual")
@click.option('--create_ansible_host', help='Will include ansible host in the Terraform manifest', default=True)
@click.option('--create_container_registry', help='Will include managed container registry in the Terraform manifest', default=True)
def generate_terraform(cwdf_config, ssh_public_key, job_id, create_ansible_host, create_container_registry):
    with open(cwdf_config, 'r') as f:
        cwdf_config = f.read()

    with open(ssh_public_key, 'r') as f:
        ssh_public_key = f.read().strip()

    tf_manifest = compose_terraform(cwdf_config, job_id, ssh_public_key, create_ansible_host, create_container_registry)
    click.echo(tf_manifest)


cli.add_command(generate_terraform)


if __name__ == "__main__":
    cli()
