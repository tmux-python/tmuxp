import logging
import os

import click
from click.exceptions import FileError

from .. import config, log
from .constants import VALID_CONFIG_DIR_FILE_EXTENSIONS

logger = logging.getLogger(__name__)


def tmuxp_echo(message=None, log_level="INFO", style_log=False, **click_kwargs):
    """
    Combines logging.log and click.echo
    """
    if style_log:
        logger.log(log.LOG_LEVELS[log_level], message)
    else:
        logger.log(log.LOG_LEVELS[log_level], click.unstyle(message))

    click.echo(message, **click_kwargs)


def get_config_dir():
    """
    Return tmuxp configuration directory.

    ``TMUXP_CONFIGDIR`` environmental variable has precedence if set. We also
    evaluate XDG default directory from XDG_CONFIG_HOME environmental variable
    if set or its default. Then the old default ~/.tmuxp is returned for
    compatibility.

    Returns
    -------
    str :
        absolute path to tmuxp config directory
    """

    paths = []
    if "TMUXP_CONFIGDIR" in os.environ:
        paths.append(os.environ["TMUXP_CONFIGDIR"])
    if "XDG_CONFIG_HOME" in os.environ:
        paths.append(os.path.join(os.environ["XDG_CONFIG_HOME"], "tmuxp"))
    else:
        paths.append("~/.config/tmuxp/")
    paths.append("~/.tmuxp")

    for path in paths:
        path = os.path.expanduser(path)
        if os.path.isdir(path):
            return path
    # Return last path as default if none of the previous ones matched
    return path


def _validate_choices(options):
    """
    Callback wrapper for validating click.prompt input.

    Parameters
    ----------
    options : list
        List of allowed choices

    Returns
    -------
    :func:`callable`
        callback function for value_proc in :func:`click.prompt`.

    Raises
    ------
    :class:`click.BadParameter`
    """

    def func(value):
        if value not in options:
            raise click.BadParameter(
                "Possible choices are: {}.".format(", ".join(options))
            )
        return value

    return func


class ConfigPath(click.Path):
    def __init__(self, config_dir=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_dir = config_dir

    def convert(self, value, param, ctx):
        config_dir = self.config_dir
        if callable(config_dir):
            config_dir = config_dir()

        value = scan_config(value, config_dir=config_dir)
        return super().convert(value, param, ctx)


def scan_config_argument(ctx, param, value, config_dir=None):
    """Validate / translate config name/path values for click config arg.

    Wrapper on top of :func:`cli.scan_config`."""
    if callable(config_dir):
        config_dir = config_dir()

    if not config:
        tmuxp_echo("Enter at least one CONFIG")
        tmuxp_echo(ctx.get_help(), color=ctx.color)
        ctx.exit()

    if isinstance(value, str):
        value = scan_config(value, config_dir=config_dir)

    elif isinstance(value, tuple):
        value = tuple(scan_config(v, config_dir=config_dir) for v in value)

    return value


def get_abs_path(config):
    path = os.path
    join, isabs = path.join, path.isabs
    dirname, normpath = path.dirname, path.normpath
    cwd = os.getcwd()

    config = os.path.expanduser(config)
    if not isabs(config) or len(dirname(config)) > 1:
        config = normpath(join(cwd, config))

    return config


def scan_config(config, config_dir=None):
    """
    Return the real config path or raise an exception.

    If config is directory, scan for .tmuxp.{yaml,yml,json} in directory. If
    one or more found, it will warn and pick the first.

    If config is ".", "./" or None, it will scan current directory.

    If config is has no path and only a filename, e.g. "myconfig.yaml" it will
    search config dir.

    If config has no path and only a name with no extension, e.g. "myconfig",
    it will scan for file name with yaml, yml and json. If multiple exist, it
    will warn and pick the first.

    Parameters
    ----------
    config : str
        config file, valid examples:

        - a file name, myconfig.yaml
        - relative path, ../config.yaml or ../project
        - a period, .

    Raises
    ------
    :class:`click.exceptions.FileError`
    """
    if not config_dir:
        config_dir = get_config_dir()
    path = os.path
    exists, join, isabs = path.exists, path.join, path.isabs
    dirname, normpath, splitext = path.dirname, path.normpath, path.splitext
    cwd = os.getcwd()
    is_name = False
    file_error = None

    config = os.path.expanduser(config)
    # if purename, resolve to confg dir
    if is_pure_name(config):
        is_name = True
    elif (
        not isabs(config)
        or len(dirname(config)) > 1
        or config == "."
        or config == ""
        or config == "./"
    ):  # if relative, fill in full path
        config = normpath(join(cwd, config))

    # no extension, scan
    if path.isdir(config) or not splitext(config)[1]:
        if is_name:
            candidates = [
                x
                for x in [
                    f"{join(config_dir, config)}{ext}"
                    for ext in VALID_CONFIG_DIR_FILE_EXTENSIONS
                ]
                if exists(x)
            ]
            if not len(candidates):
                file_error = (
                    "config not found in config dir (yaml/yml/json) %s "
                    "for name" % (config_dir)
                )
        else:
            candidates = [
                x
                for x in [
                    join(config, ext)
                    for ext in [".tmuxp.yaml", ".tmuxp.yml", ".tmuxp.json"]
                ]
                if exists(x)
            ]

            if len(candidates) > 1:
                tmuxp_echo(
                    click.style(
                        "Multiple .tmuxp.{yml,yaml,json} configs in %s"
                        % dirname(config),
                        fg="red",
                    )
                )
                tmuxp_echo(
                    click.wrap_text(
                        "This is undefined behavior, use only one. "
                        "Use file names e.g. myproject.json, coolproject.yaml. "
                        "You can load them by filename."
                    )
                )
            elif not len(candidates):
                file_error = "No tmuxp files found in directory"
        if len(candidates):
            config = candidates[0]
    elif not exists(config):
        file_error = "file not found"

    if file_error:
        raise FileError(file_error, config)

    return config


def is_pure_name(path):
    """
    Return True if path is a name and not a file path.

    Parameters
    ----------
    path : str
        Path (can be absolute, relative, etc.)

    Returns
    -------
    bool
        True if path is a name of config in config dir, not file path.
    """
    return (
        not os.path.isabs(path)
        and len(os.path.dirname(path)) == 0
        and not os.path.splitext(path)[1]
        and path != "."
        and path != ""
    )
