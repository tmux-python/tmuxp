import os

from sniffer.api import runnable, file_validator


@file_validator
def py_files(filename):
    return (filename.endswith('.rst') or filename.endswith('Makefile')) and not os.path.basename(filename).startswith('.')


@runnable
def execute_nose(*args):
    from subprocess import call
    if len(args) > 1:
        return call('make %s' % args[1], shell=True) == 0
    else:
        return call('make html', shell=True) == 0
