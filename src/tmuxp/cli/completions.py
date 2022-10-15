import os

from libtmux.server import Server
from tmuxp import config
from tmuxp.cli.utils import get_config_dir

config_dir = get_config_dir()

try:
    import argcomplete
except ImportError:

    class ArgComplete:
        class Completers:
            class Completer:
                def __call__(self, *args: object, **kwargs: object) -> object:
                    ...

            FilesCompleter = Completer

        completers = Completers()

    argcomplete = ArgComplete()  # type:ignore


class ConfigFileCompleter(argcomplete.completers.FilesCompleter):

    """argcomplete completer for tmuxp files."""

    def __call__(self, prefix, **kwargs):

        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )

        completion += [os.path.join(config_dir, c) for c in config.in_dir(config_dir)]

        return completion


class TmuxinatorCompleter(argcomplete.completers.FilesCompleter):

    """argcomplete completer for Tmuxinator files."""

    def __call__(self, prefix, **kwargs):
        from tmuxp.cli.import_config import get_tmuxinator_dir

        tmuxinator_config_dir = get_tmuxinator_dir()
        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )
        tmuxinator_configs = config.in_dir(tmuxinator_config_dir, extensions="yml")
        completion += [
            os.path.join(tmuxinator_config_dir, f) for f in tmuxinator_configs
        ]

        return completion


class TeamocilCompleter(argcomplete.completers.FilesCompleter):

    """argcomplete completer for Teamocil files."""

    def __call__(self, prefix, **kwargs):
        from tmuxp.cli.import_config import get_teamocil_dir

        teamocil_config_dir = get_teamocil_dir()

        completion = argcomplete.completers.FilesCompleter.__call__(
            self, prefix, **kwargs
        )
        teamocil_configs = config.in_dir(teamocil_config_dir, extensions="yml")
        completion += [os.path.join(teamocil_config_dir, f) for f in teamocil_configs]

        return completion


def SessionCompleter(prefix, parsed_args, **kwargs):
    """Return list of session names for argcomplete completer."""

    t = Server(socket_name=parsed_args.socket_name, socket_path=parsed_args.socket_path)

    sessions_available = [
        s.get("session_name")
        for s in t._sessions
        if s.get("session_name").startswith(" ".join(prefix))
    ]

    if parsed_args.session_name and sessions_available:
        return []

    return [
        s.get("session_name")
        for s in t._sessions
        if s.get("session_name").startswith(prefix)
    ]
