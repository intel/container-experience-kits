import click
import git


class CloneProgress(git.RemoteProgress):
    """
    Class for logging the output from Git clone.
    """

    def update(self, op_code, cur_count, max_count=None, message=''):
        """
        Takes output from Git clone and wrote it to console.

        op_code (-): Not used
        cur_count (-): Not used
        max_count (-): Not used
        message (string): String with information to print

        Return:
        None

        """
        if message:
            click.echo(message)


def clone_repository(clone_dir, repo_url, branch, token):
    """
    Cloning a Git repository with the ability to specify a specific branch.

    Parameters:
    clone_dir (string): Path where to clone git repository
    repo_url (string): URL address of git repository
    branch (string): Name of the branch to checkout
    token (string): Personal access token for non public repository

    Return:
    None

    """
    click.echo('GIT clone:')
    # print the url BEFORE replacing the security token, to avoid printing the token
    click.echo(f"Repository URL: {repo_url}")
    click.echo(f"Repository local path: {clone_dir}")

    if token is not None and "<token>@" in repo_url:
        repo_url = repo_url.replace("<token>", token)
    else:
        repo_url = repo_url.replace("<token>@", "")

    if branch is not None:
        return git.Repo.clone_from(url=repo_url,
                                   to_path=clone_dir,
                                   single_branch=True,
                                   branch=branch,
                                   progress=CloneProgress())
    else:
        return git.Repo.clone_from(url=repo_url,
                                   to_path=clone_dir,
                                   single_branch=True,
                                   progress=CloneProgress())


def switch_repository_to_tag(repo, tag):
    """
    Changing the repository version to specific tag.

    Parameters:
    repo (git obj): PythonGit obj of cloned repository
    tag (string): Name of tag to checkout

    Return:
    None

    """
    for list_tag in repo.tags:
        if tag in str(list_tag):
            repo.git.checkout(tag)
            click.echo("Cloned repository was checkout to tag %s", tag)
