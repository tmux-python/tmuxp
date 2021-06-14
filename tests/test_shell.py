from tmuxp import shell


def test_detect_best_shell():
    result = shell.detect_best_shell()
    assert isinstance(result, str)


def test_shell_detect():
    assert isinstance(shell.has_bpython(), bool)
    assert isinstance(shell.has_ipython(), bool)
    assert isinstance(shell.has_ptpython(), bool)
    assert isinstance(shell.has_ptipython(), bool)
