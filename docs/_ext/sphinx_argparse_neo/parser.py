"""Argparse introspection - extract structured data from ArgumentParser.

This module provides dataclasses and functions to introspect argparse
ArgumentParser instances and convert them into structured data suitable
for documentation rendering.
"""

from __future__ import annotations

import argparse
import dataclasses
import typing as t

# Sentinel for "no default" (distinct from None which is a valid default)
NO_DEFAULT = object()


@dataclasses.dataclass
class ArgumentInfo:
    """Represents a single CLI argument.

    Examples
    --------
    >>> info = ArgumentInfo(
    ...     names=["-v", "--verbose"],
    ...     help="Enable verbose output",
    ...     default=False,
    ...     default_string="False",
    ...     choices=None,
    ...     required=False,
    ...     metavar=None,
    ...     nargs=None,
    ...     action="store_true",
    ...     type_name=None,
    ...     const=True,
    ...     dest="verbose",
    ... )
    >>> info.names
    ['-v', '--verbose']
    >>> info.is_positional
    False
    """

    names: list[str]
    help: str | None
    default: t.Any
    default_string: str | None
    choices: list[t.Any] | None
    required: bool
    metavar: str | None
    nargs: str | int | None
    action: str
    type_name: str | None
    const: t.Any
    dest: str

    @property
    def is_positional(self) -> bool:
        """Return True if this is a positional argument.

        Examples
        --------
        >>> ArgumentInfo(
        ...     names=["filename"],
        ...     help=None,
        ...     default=None,
        ...     default_string=None,
        ...     choices=None,
        ...     required=True,
        ...     metavar=None,
        ...     nargs=None,
        ...     action="store",
        ...     type_name=None,
        ...     const=None,
        ...     dest="filename",
        ... ).is_positional
        True
        >>> ArgumentInfo(
        ...     names=["-f", "--file"],
        ...     help=None,
        ...     default=None,
        ...     default_string=None,
        ...     choices=None,
        ...     required=False,
        ...     metavar=None,
        ...     nargs=None,
        ...     action="store",
        ...     type_name=None,
        ...     const=None,
        ...     dest="file",
        ... ).is_positional
        False
        """
        return bool(self.names) and not self.names[0].startswith("-")


@dataclasses.dataclass
class MutuallyExclusiveGroup:
    """Arguments that cannot be used together.

    Examples
    --------
    >>> group = MutuallyExclusiveGroup(arguments=[], required=True)
    >>> group.required
    True
    """

    arguments: list[ArgumentInfo]
    required: bool


@dataclasses.dataclass
class ArgumentGroup:
    """Named group of arguments.

    Examples
    --------
    >>> group = ArgumentGroup(
    ...     title="Output Options",
    ...     description="Control output format",
    ...     arguments=[],
    ...     mutually_exclusive=[],
    ... )
    >>> group.title
    'Output Options'
    """

    title: str
    description: str | None
    arguments: list[ArgumentInfo]
    mutually_exclusive: list[MutuallyExclusiveGroup]


@dataclasses.dataclass
class SubcommandInfo:
    """A subparser/subcommand.

    Examples
    --------
    >>> sub = SubcommandInfo(
    ...     name="sync",
    ...     aliases=["s"],
    ...     help="Synchronize repositories",
    ...     parser=None,  # type: ignore[arg-type]
    ... )
    >>> sub.aliases
    ['s']
    """

    name: str
    aliases: list[str]
    help: str | None
    parser: ParserInfo  # Recursive reference


@dataclasses.dataclass
class ParserInfo:
    """Complete parsed ArgumentParser.

    Examples
    --------
    >>> info = ParserInfo(
    ...     prog="myapp",
    ...     usage=None,
    ...     bare_usage="myapp [-h] command",
    ...     description="My application",
    ...     epilog=None,
    ...     argument_groups=[],
    ...     subcommands=None,
    ...     subcommand_dest=None,
    ... )
    >>> info.prog
    'myapp'
    """

    prog: str
    usage: str | None
    bare_usage: str
    description: str | None
    epilog: str | None
    argument_groups: list[ArgumentGroup]
    subcommands: list[SubcommandInfo] | None
    subcommand_dest: str | None


def _format_default(default: t.Any) -> str | None:
    """Format a default value for display.

    Parameters
    ----------
    default : t.Any
        The default value to format.

    Returns
    -------
    str | None
        Formatted string representation, or None if suppressed/unset.

    Examples
    --------
    >>> _format_default(None)
    'None'
    >>> _format_default("hello")
    'hello'
    >>> _format_default(42)
    '42'
    >>> _format_default(argparse.SUPPRESS) is None
    True
    >>> _format_default([1, 2, 3])
    '[1, 2, 3]'
    """
    if default is argparse.SUPPRESS:
        return None
    if default is None:
        return "None"
    if isinstance(default, str):
        return default
    return repr(default)


def _get_type_name(action: argparse.Action) -> str | None:
    """Extract the type name from an action.

    Parameters
    ----------
    action : argparse.Action
        The argparse action to inspect.

    Returns
    -------
    str | None
        The type name, or None if no type is specified.

    Examples
    --------
    >>> parser = argparse.ArgumentParser()
    >>> action = parser.add_argument("--count", type=int)
    >>> _get_type_name(action)
    'int'
    >>> action2 = parser.add_argument("--name")
    >>> _get_type_name(action2) is None
    True
    """
    if action.type is None:
        return None
    if hasattr(action.type, "__name__"):
        return action.type.__name__
    return str(action.type)


def _get_action_name(action: argparse.Action) -> str:
    """Get the action type name.

    Parameters
    ----------
    action : argparse.Action
        The argparse action to inspect.

    Returns
    -------
    str
        The action type name.

    Examples
    --------
    >>> parser = argparse.ArgumentParser()
    >>> action = parser.add_argument("--verbose", action="store_true")
    >>> _get_action_name(action)
    'store_true'
    >>> action2 = parser.add_argument("--file")
    >>> _get_action_name(action2)
    'store'
    """
    # Map action classes to their string names
    action_class = type(action).__name__
    action_map = {
        "_StoreAction": "store",
        "_StoreTrueAction": "store_true",
        "_StoreFalseAction": "store_false",
        "_StoreConstAction": "store_const",
        "_AppendAction": "append",
        "_AppendConstAction": "append_const",
        "_CountAction": "count",
        "_HelpAction": "help",
        "_VersionAction": "version",
        "_ExtendAction": "extend",
        "BooleanOptionalAction": "boolean_optional",
    }
    return action_map.get(action_class, action_class.lower())


def _extract_argument(action: argparse.Action) -> ArgumentInfo:
    """Extract ArgumentInfo from an argparse Action.

    Parameters
    ----------
    action : argparse.Action
        The argparse action to extract information from.

    Returns
    -------
    ArgumentInfo
        Structured argument information.

    Examples
    --------
    >>> parser = argparse.ArgumentParser()
    >>> action = parser.add_argument(
    ...     "-v", "--verbose",
    ...     action="store_true",
    ...     help="Enable verbose mode",
    ... )
    >>> info = _extract_argument(action)
    >>> info.names
    ['-v', '--verbose']
    >>> info.action
    'store_true'
    """
    # Determine names - option_strings for optionals, dest for positionals
    names = list(action.option_strings) if action.option_strings else [action.dest]

    # Determine if required
    required = action.required if hasattr(action, "required") else False
    # Positional arguments are required by default (unless nargs makes them optional)
    if not action.option_strings:
        required = action.nargs not in ("?", "*", argparse.REMAINDER)

    # Format metavar
    metavar = action.metavar
    if isinstance(metavar, tuple):
        metavar = " ".join(metavar)

    # Handle default
    default = action.default
    default_string = _format_default(default)

    return ArgumentInfo(
        names=names,
        help=action.help if action.help != argparse.SUPPRESS else None,
        default=default if default is not argparse.SUPPRESS else NO_DEFAULT,
        default_string=default_string,
        choices=list(action.choices) if action.choices else None,
        required=required,
        metavar=metavar,
        nargs=action.nargs,
        action=_get_action_name(action),
        type_name=_get_type_name(action),
        const=action.const,
        dest=action.dest,
    )


def _extract_mutex_groups(
    parser: argparse.ArgumentParser,
) -> dict[int, MutuallyExclusiveGroup]:
    """Extract mutually exclusive groups from a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to extract from.

    Returns
    -------
    dict[int, MutuallyExclusiveGroup]
        Mapping from action id to the MutuallyExclusiveGroup it belongs to.
    """
    mutex_map: dict[int, MutuallyExclusiveGroup] = {}

    for mutex_group in parser._mutually_exclusive_groups:
        group_info = MutuallyExclusiveGroup(
            arguments=[
                _extract_argument(action)
                for action in mutex_group._group_actions
                if action.help != argparse.SUPPRESS
            ],
            required=mutex_group.required,
        )
        for action in mutex_group._group_actions:
            mutex_map[id(action)] = group_info

    return mutex_map


def _extract_argument_groups(
    parser: argparse.ArgumentParser,
    hide_suppressed: bool = True,
) -> list[ArgumentGroup]:
    """Extract argument groups from a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to extract from.
    hide_suppressed : bool
        Whether to hide arguments with SUPPRESS help.

    Returns
    -------
    list[ArgumentGroup]
        List of argument groups.

    Examples
    --------
    >>> parser = argparse.ArgumentParser(description="Test")
    >>> _ = parser.add_argument("filename", help="Input file")
    >>> _ = parser.add_argument("-v", "--verbose", action="store_true")
    >>> groups = _extract_argument_groups(parser)
    >>> len(groups) >= 2  # positional and optional groups
    True
    """
    mutex_map = _extract_mutex_groups(parser)
    seen_mutex: set[int] = set()
    groups: list[ArgumentGroup] = []

    for group in parser._action_groups:
        arguments: list[ArgumentInfo] = []
        mutex_groups: list[MutuallyExclusiveGroup] = []

        for action in group._group_actions:
            # Skip help action and suppressed actions
            if isinstance(action, argparse._HelpAction):
                continue
            if hide_suppressed and action.help == argparse.SUPPRESS:
                continue
            # Skip subparser actions - handled separately
            if isinstance(action, argparse._SubParsersAction):
                continue

            # Check if this action is in a mutex group
            if id(action) in mutex_map:
                mutex_info = mutex_map[id(action)]
                mutex_id = id(mutex_info)
                if mutex_id not in seen_mutex:
                    seen_mutex.add(mutex_id)
                    mutex_groups.append(mutex_info)
            else:
                arguments.append(_extract_argument(action))

        # Skip empty groups
        if not arguments and not mutex_groups:
            continue

        groups.append(
            ArgumentGroup(
                title=group.title or "",
                description=group.description,
                arguments=arguments,
                mutually_exclusive=mutex_groups,
            )
        )

    return groups


def _extract_subcommands(
    parser: argparse.ArgumentParser,
    hide_suppressed: bool = True,
) -> tuple[list[SubcommandInfo] | None, str | None]:
    """Extract subcommands from a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to extract from.
    hide_suppressed : bool
        Whether to hide subcommands with SUPPRESS help.

    Returns
    -------
    tuple[list[SubcommandInfo] | None, str | None]
        Tuple of (subcommands list, destination variable name).

    Examples
    --------
    >>> parser = argparse.ArgumentParser()
    >>> subparsers = parser.add_subparsers(dest="command")
    >>> _ = subparsers.add_parser("sync", help="Sync repos")
    >>> _ = subparsers.add_parser("add", help="Add repo")
    >>> subs, dest = _extract_subcommands(parser)
    >>> dest
    'command'
    >>> len(subs)
    2
    """
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subcommands: list[SubcommandInfo] = []

            # Get the choices (subparsers)
            choices = action.choices or {}

            # Build reverse mapping of aliases
            # action._parser_class might have name_parser_map with aliases
            alias_map: dict[str, list[str]] = {}
            seen_parsers: dict[int, str] = {}

            for name, subparser in choices.items():
                parser_id = id(subparser)
                if parser_id in seen_parsers:
                    # This is an alias
                    primary = seen_parsers[parser_id]
                    if primary not in alias_map:
                        alias_map[primary] = []
                    alias_map[primary].append(name)
                else:
                    seen_parsers[parser_id] = name

            # Now extract subcommand info
            processed: set[int] = set()
            for name, subparser in choices.items():
                parser_id = id(subparser)
                if parser_id in processed:
                    continue
                processed.add(parser_id)

                # Get help text
                help_text: str | None = None
                if hasattr(action, "_choices_actions"):
                    for choice_action in action._choices_actions:
                        if choice_action.dest == name:
                            help_text = choice_action.help
                            break

                if hide_suppressed and help_text == argparse.SUPPRESS:
                    continue

                # Recursively extract parser info
                sub_info = extract_parser(subparser, hide_suppressed=hide_suppressed)

                subcommands.append(
                    SubcommandInfo(
                        name=name,
                        aliases=alias_map.get(name, []),
                        help=help_text,
                        parser=sub_info,
                    )
                )

            return subcommands, action.dest

    return None, None


def _generate_usage(parser: argparse.ArgumentParser) -> str:
    """Generate the usage string for a parser.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to generate usage for.

    Returns
    -------
    str
        The bare usage string (without "usage: " prefix).

    Examples
    --------
    >>> parser = argparse.ArgumentParser(prog="myapp")
    >>> _ = parser.add_argument("-v", "--verbose", action="store_true")
    >>> usage = _generate_usage(parser)
    >>> "myapp" in usage
    True
    """
    # Use argparse's built-in formatter to generate usage
    formatter = parser._get_formatter()
    formatter.add_usage(
        parser.usage, parser._actions, parser._mutually_exclusive_groups
    )
    usage = formatter.format_help().strip()

    # Remove "usage: " prefix if present
    if usage.lower().startswith("usage:"):
        usage = usage[6:].strip()

    return usage


def extract_parser(
    parser: argparse.ArgumentParser,
    hide_suppressed: bool = True,
) -> ParserInfo:
    """Extract complete parser information.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The parser to extract information from.
    hide_suppressed : bool
        Whether to hide arguments/subcommands with SUPPRESS help.

    Returns
    -------
    ParserInfo
        Complete structured parser information.

    Examples
    --------
    >>> parser = argparse.ArgumentParser(
    ...     prog="myapp",
    ...     description="My application",
    ... )
    >>> _ = parser.add_argument("filename", help="Input file")
    >>> _ = parser.add_argument("-v", "--verbose", action="store_true")
    >>> info = extract_parser(parser)
    >>> info.prog
    'myapp'
    >>> info.description
    'My application'
    >>> len(info.argument_groups) >= 1
    True
    """
    subcommands, subcommand_dest = _extract_subcommands(parser, hide_suppressed)

    return ParserInfo(
        prog=parser.prog,
        usage=parser.usage,
        bare_usage=_generate_usage(parser),
        description=parser.description,
        epilog=parser.epilog,
        argument_groups=_extract_argument_groups(parser, hide_suppressed),
        subcommands=subcommands,
        subcommand_dest=subcommand_dest,
    )
