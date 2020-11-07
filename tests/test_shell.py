from tmuxp import shell
from tmuxp._compat import string_types


def test_detect_best_shell():
    result = shell.detect_best_shell()
    assert isinstance(result, string_types)


def test_shell_detect():
    assert isinstance(shell.has_bpython(), bool)
    assert isinstance(shell.has_ipython(), bool)
    assert isinstance(shell.has_ptpython(), bool)
    assert isinstance(shell.has_ptipython(), bool)
