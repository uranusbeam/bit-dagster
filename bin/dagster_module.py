import contextlib
import fnmatch
import os
import subprocess
import sys
from collections import namedtuple

import click
import six

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, BASE_PATH)

from git_utils import git_repo_root  # isort:skip

# We don't want to accidentally publish cruft in these directories
CRUFTY_DIRECTORIES = ['.tox', 'build', 'dist', '*.egg-info', '__pycache__', '.pytest_cache']


class DagsterModule(namedtuple('_DagsterModule', 'name is_library additional_steps')):
    '''Represents a Dagster module we publish to PyPI.

    Args:
        name (str): Name of the module. Should be found under python_modules/ or under
            python_modules/libraries/
        is_library (bool): True for libraries, False for core modules.
        should_publish (bool): Whether this module should be published to PyPI
        additional_steps (List[str]): Any additional publish steps
    '''

    def __new__(cls, name, is_library=False, additional_steps=None):
        return super(DagsterModule, cls).__new__(cls, name, is_library, additional_steps)

    @property
    def module_path(self):
        git_root = git_repo_root()
        if self.is_library:
            return os.path.join(git_root, 'python_modules', 'libraries', self.name)
        else:
            return os.path.join(git_root, 'python_modules', self.name)

    @property
    def version_file_path(self):
        '''Absolute path to this module's version.py file.
        '''
        return os.path.join(self.module_path, self.normalized_module_name, 'version.py')

    @property
    def should_publish(self):
        '''Only packages with a version.py file should be published.
        '''
        return os.path.exists(self.version_file_path)

    @property
    def normalized_module_name(self):
        '''Our package convention is to find the source for module foo_bar in foo-bar/foo_bar.'''
        return self.name.replace('-', '_')

    @contextlib.contextmanager
    def pushd_module(self):
        '''Context manager that sets the current working directory to the root of this module. Will
        reset to original working directory on close.

        Yields:
            str: The path of the module
        '''
        old_cwd = os.getcwd()
        new_cwd = self.module_path
        os.chdir(new_cwd)
        try:
            yield new_cwd
        finally:
            os.chdir(old_cwd)

    def find_cruft(self):
        '''Returns a list of "crufty" directories found within this module.

        Returns:
            List[str]: List of crufty directories
        '''
        cruft = []
        for dir_ in os.listdir(self.module_path):
            for potential_cruft in CRUFTY_DIRECTORIES:
                if fnmatch.fnmatch(dir_, potential_cruft):
                    cruft.append(os.path.join(self.module_path, dir_))
        return cruft

    def get_version_info(self):
        '''Extract module version information from the module's version.py file.

        Returns:
            Dict[str, str]: Dictionary of version information.
        '''
        module_version = {}
        with open(self.version_file_path) as fp:
            exec(fp.read(), module_version)  # pylint: disable=W0122

        assert (
            '__version__' in module_version and '__nightly__' in module_version
        ), 'Bad version for module {name}'.format(name=self.name)

        return {
            '__version__': module_version['__version__'],
            '__nightly__': module_version['__nightly__'],
        }

    def set_version_info(self, new_version, new_nightly, dry_run=True):
        '''Updates this modules version.py file with a new version and nightly version.

        Returns:
            Dict[str, str]: Dictionary of version information.
        '''
        assert isinstance(new_version, six.string_types)
        assert isinstance(new_nightly, six.string_types)

        output = (
            '__version__ = \'{new_version}\'\n'
            '\n'
            '__nightly__ = \'{new_nightly}\'\n'.format(
                new_version=new_version, new_nightly=new_nightly
            )
        )

        version_file = self.version_file_path

        if dry_run:
            click.echo(
                click.style('Dry run; not running. Would write to: %s\n' % version_file, fg='red')
                + output
                + '\n'
            )
        else:
            with open(version_file, 'w') as fd:
                fd.write(output)

        return {'__version__': new_version, '__nightly__': new_nightly}

    def publish(self, nightly=False, dry_run=True):
        '''Publish this module to PyPI.

        Args:
            nightly (bool, optional): Set if this is a nightly build vs. prod release. Defaults to
                False.
            dry_run (bool, optional): If a dry run, will echo and won't actually run the publish
                commands. Defaults to True.
        '''
        with self.pushd_module() as cwd:
            for command in construct_publish_comands(
                additional_steps=self.additional_steps, nightly=nightly
            ):
                if dry_run:
                    click.echo(
                        click.style('Dry run; not running.', fg='red')
                        + ' Would run {cwd}:$ {cmd}'.format(cmd=command, cwd=cwd)
                    )
                else:
                    click.echo('About to run command {cwd}:$ {cmd}'.format(cmd=command, cwd=cwd))
                    process = subprocess.Popen(
                        command, stderr=subprocess.PIPE, cwd=cwd, shell=True, stdout=subprocess.PIPE
                    )
                    for line in iter(process.stdout.readline, b''):
                        click.echo(line.decode('utf-8'))

                    for line in iter(process.stderr.readline, b''):
                        click.echo(line.decode('utf-8'))

                    process.wait()
                    assert process.returncode == 0, (
                        'Something went wrong while attempting to publish module {module_name}! '
                        'Got code {code} from command "{command}" in cwd {cwd}'.format(
                            module_name=self.name, code=process.returncode, command=command, cwd=cwd
                        )
                    )


def construct_publish_comands(additional_steps=None, nightly=False):
    '''Get the shell commands we'll use to actually build and publish a package to PyPI.

    Returns:
        List[str]: List of shell commands needed to publish a module.
    '''

    nightly = ' --nightly' if nightly else ''

    return (additional_steps or []) + [
        'python setup.py sdist bdist_wheel{nightly}'.format(nightly=nightly),
        'twine upload --verbose dist/*',
    ]
