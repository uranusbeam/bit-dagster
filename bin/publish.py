#!/usr/bin/env python3

"""Tools to manage tagging and publishing releases of the Dagster projects.

Please follow the checklist in RELEASING.md at the root of this repository.

For detailed usage instructions, please consult the command line help,
available by running `python publish.py --help`.
"""
# distutils issue: https://github.com/PyCQA/pylint/issues/73

import os
import subprocess
import sys
import tempfile
import urllib

import click
import packaging.version
import requests
import slackclient
import virtualenv
from dagster_module_publisher import DagsterModulePublisher

from git_utils import (  # isort:skip
    get_most_recent_git_tag,
    git_check_status,
    git_push,
    git_user,
    set_git_tag,
)

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, BASE_PATH)

from publish_utils import format_module_versions, which_  # isort:skip
from pypirc import ConfigFileError, RCParser  # isort:skip


CLI_HELP = '''Tools to help tag and publish releases of the Dagster projects.

By convention, these projects live in a single monorepo, and the submodules are versioned in
lockstep to avoid confusion, i.e., if dagster is at 0.3.0, dagit is also expected to be at
0.3.0.

Versions are tracked in the version.py files present in each submodule and in the git tags
applied to the repository as a whole. These tools help ensure that these versions do not drift.
'''


PYPIRC_EXCEPTION_MESSAGE = '''You must have credentials available to PyPI in the form of a
~/.pypirc file (see: https://docs.python.org/2/distutils/packageindex.html#pypirc):

    [distutils]
    index-servers =
        pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>
'''


@click.group(help=CLI_HELP)
def cli():
    pass


@cli.command()
@click.option('--nightly', is_flag=True)
@click.option('--autoclean', is_flag=True)
@click.option('--dry-run', is_flag=True)
def publish(nightly, autoclean, dry_run):
    '''Publishes (uploads) all submodules to PyPI.

    Appropriate credentials must be available to twine, e.g. in a ~/.pypirc file, and users must
    be permissioned as maintainers on the PyPI projects. Publishing will fail if versions (git
    tags and Python versions) are not in lockstep, if the current commit is not tagged, or if
    there are untracked changes.
    '''
    assert os.getenv('SLACK_RELEASE_BOT_TOKEN'), 'No SLACK_RELEASE_BOT_TOKEN env variable found.'

    try:
        RCParser.from_file()
    except ConfigFileError:
        raise ConfigFileError(PYPIRC_EXCEPTION_MESSAGE)

    assert '\nwheel' in subprocess.check_output(['pip', 'list']).decode('utf-8'), (
        'You must have wheel installed in order to build packages for release -- run '
        '`pip install wheel`.'
    )

    assert which_('twine'), (
        'You must have twine installed in order to upload packages to PyPI -- run '
        '`pip install twine`.'
    )

    assert which_('yarn'), (
        'You must have yarn installed in order to build dagit for release -- see '
        'https://yarnpkg.com/lang/en/docs/install/'
    )
    dmp = DagsterModulePublisher()

    checked_version = dmp.check_versions(nightly=nightly)
    if not nightly:
        click.echo('... and match git tag on most recent commit...')
        git_check_status()
    click.echo('... and that there is no cruft present...')
    dmp.check_for_cruft(autoclean)
    click.echo('... and that the directories look like we expect')
    dmp.check_directory_structure()

    click.echo('Publishing packages to PyPI...')

    if nightly:
        new_nightly_version = dmp.set_version_info(dry_run=dry_run)['__nightly__']
        dmp.commit_new_version(
            'nightly: {nightly}'.format(nightly=new_nightly_version), dry_run=dry_run
        )
        tag = set_git_tag('nightly-{ver}'.format(ver=new_nightly_version), dry_run=dry_run)
        git_push(dry_run=dry_run)
        git_push(tag, dry_run=dry_run)

    dmp.publish_all(nightly, dry_run=dry_run)

    if not nightly:
        parsed_version = packaging.version.parse(checked_version['__version__'])
        if not parsed_version.is_prerelease and not dry_run:
            slack_client = slackclient.SlackClient(os.environ['SLACK_RELEASE_BOT_TOKEN'])
            slack_client.api_call(
                'chat.postMessage',
                channel='#general',
                text=('{git_user} just published a new version: {version}.').format(
                    git_user=git_user(), version=checked_version['__version__']
                ),
            )


@cli.command()
@click.argument('ver')
@click.option('--dry-run', is_flag=True)
def release(ver, dry_run):
    '''Tags all submodules for a new release.

    Ensures that git tags, as well as the version.py files in each submodule, agree and that the
    new version is strictly greater than the current version. Will fail if the new version
    is not an increment (following PEP 440). Creates a new git tag and commit.
    '''
    dmp = DagsterModulePublisher()
    dmp.check_new_version(ver)
    dmp.set_version_info(new_version=ver, dry_run=dry_run)
    dmp.commit_new_version(ver, dry_run=dry_run)
    set_git_tag(ver, dry_run=dry_run)
    click.echo(
        'Successfully set new version and created git tag {version}. You may continue with the '
        'release checklist.'.format(version=ver)
    )


@cli.command()
def version():
    '''Gets the most recent tagged version.'''
    dmp = DagsterModulePublisher()

    module_versions = dmp.check_all_versions_equal()
    git_tag = get_most_recent_git_tag()
    parsed_version = packaging.version.parse(git_tag)
    errors = {}
    for module_name, module_version in module_versions.items():
        if packaging.version.parse(module_version['__version__']) > parsed_version:
            errors[module_name] = module_version['__version__']
    if errors:
        click.echo(
            'Warning: Found modules with existing versions that did not match the most recent '
            'tagged version {git_tag}:\n{versions}'.format(
                git_tag=git_tag, versions=format_module_versions(module_versions)
            )
        )
    else:
        click.echo(
            'All modules in lockstep with most recent tagged version: {git_tag}'.format(
                git_tag=git_tag
            )
        )


@cli.command()
@click.argument('version')
def audit(version):  # pylint: disable=redefined-outer-name
    '''Checks that the given version is installable from PyPI in a new virtualenv.'''
    dmp = DagsterModulePublisher()

    for module in dmp.all_publishable_modules:
        res = requests.get(
            urllib.parse.urlunparse(
                ('https', 'pypi.org', '/'.join(['pypi', module.name, 'json']), None, None, None)
            )
        )
        module_json = res.json()
        assert (
            version in module_json['releases']
        ), 'Version not available for module {module_name}, expected {expected}, released version is {received}'.format(
            module_name=module, expected=version, received=module_json['info']['version']
        )

    bootstrap_text = '''
def after_install(options, home_dir):
    for module_name in [{module_names}]:
        subprocess.check_output([
            os.path.join(home_dir, 'bin', 'pip'), 'install', '{{module}}=={version}'.format(
                module=module_name
            )
        ])

'''.format(
        module_names=', '.join(
            [
                '\'{module_name}\''.format(module_name=module.name)
                for module in dmp.all_publishable_modules
            ]
        ),
        version=version,
    )

    bootstrap_script = virtualenv.create_bootstrap_script(bootstrap_text)

    with tempfile.TemporaryDirectory() as venv_dir:
        with tempfile.NamedTemporaryFile('w') as bootstrap_script_file:
            bootstrap_script_file.write(bootstrap_script)

            args = ['python', bootstrap_script_file.name, venv_dir]

            click.echo(subprocess.check_output(args).decode('utf-8'))


if __name__ == '__main__':
    click_cli = click.CommandCollection(sources=[cli], help=CLI_HELP)
    click_cli()
