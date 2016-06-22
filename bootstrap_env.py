#!/usr/bin/env python

from __future__ import absolute_import, print_function, unicode_literals

import os
import subprocess
import sys


def warning(*objs):
    print("WARNING: ", *objs, file=sys.stderr)


def fail(message):
    sys.exit("Error: {message}".format(message=message))


def has_module(module_name):
    try:
        import imp
        imp.find_module(module_name)
        del imp
        return True
    except ImportError:
        return False


def which(exe=None, throw=True):
    """Return path of bin. Python clone of /usr/bin/which.

    from salt.util - https://www.github.com/saltstack/salt - license apache

    :param exe: Application to search PATHs for.
    :type exe: string
    :param throw: Raise ``Exception`` if not found in paths
    :type throw: bool
    :rtype: string

    """
    if exe:
        if os.access(exe, os.X_OK):
            return exe

        # default path based on busybox's default
        default_path = '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin'
        search_path = os.environ.get('PATH', default_path)

        for path in search_path.split(os.pathsep):
            full_path = os.path.join(path, exe)
            if os.access(full_path, os.X_OK):
                return full_path

        message = (
            '{0!r} could not be found in the following search '
            'path: {1!r}'.format(
                exe, search_path
            )
        )

        if throw:
            raise Exception(message)
        else:
            print(message)
    return None


project_dir = os.path.dirname(os.path.realpath(__file__))
env_dir = os.path.join(project_dir, '.venv')
pip_bin = os.path.join(env_dir, 'bin', 'pip')
python_bin = os.path.join(env_dir, 'bin', 'python')
virtualenv_bin = which('virtualenv', throw=False)
virtualenv_exists = os.path.exists(env_dir) and os.path.isfile(python_bin)
sphinx_requirements_filepath = os.path.join(
    project_dir, 'requirements', 'doc.txt')
test_requirements_filepath = os.path.join(
    project_dir, 'requirements', 'test.txt')


try:
    import virtualenv  # NOQA
except ImportError:
    message = (
        'Virtualenv is required for this bootstrap to run.\n'
        'Install virtualenv via:\n'
        '\t$ [sudo] pip install virtualenv'
    )
    fail(message)


try:
    import pip  # NOQA
except ImportError:
    message = (
        'pip is required for this bootstrap to run.\n'
        'Find instructions on how to install at: %s' %
        'http://pip.readthedocs.io/en/latest/installing.html'
    )
    fail(message)


def main():
    if not which('entr', throw=False):
        message = (
            '\nentr(1) is used in this app as a cross platform file watcher.'
            'You can install it via your package manager on most POSIX '
            'systems. See the site at http://entrproject.org/\n'
        )
        print(message)

    if not virtualenv_exists:
        virtualenv_bin = which('virtualenv', throw=False)

        subprocess.check_call(
            [virtualenv_bin, env_dir]
        )

        subprocess.check_call(
            [pip_bin, 'install', '-e', project_dir]
        )

    if not has_module('pytest'):
        subprocess.check_call(
            [pip_bin, 'install', '-r', test_requirements_filepath]
        )

    if not os.path.isfile(os.path.join(env_dir, 'bin', 'sphinx-quickstart')):
        subprocess.check_call(
            [pip_bin, 'install', '-r', sphinx_requirements_filepath]
        )

    if os.path.exists(os.path.join(env_dir, 'build')):
        os.removedirs(os.path.join(env_dir, 'build'))

if __name__ == '__main__':
    main()
