# -*- coding: utf-8 -*-
"""
   click_default_group
   ~~~~~~~~~~~~~~~~~~~

   Site: https://github.com/sublee/click-default-group
   License: BSD 3 clause
     https://github.com/sublee/click-default-group/blob/master/LICENSE

   Define a default subcommand by `default=True`:
   .. sourcecode:: python
      import click
      from click_default_group import DefaultGroup
      @click.group(cls=DefaultGroup, default_if_no_args=True)
      def cli():
          pass
      @cli.command(default=True)
      def foo():
          click.echo('foo')
      @cli.command()
      def bar():
          click.echo('bar')
   Then you can invoke that without explicit subcommand name:
   .. sourcecode:: console
      $ cli.py --help
      Usage: cli.py [OPTIONS] COMMAND [ARGS]...
      Options:
        --help    Show this message and exit.
      Command:
        foo*
        bar
      $ cli.py
      foo
      $ cli.py foo
      foo
      $ cli.py bar
      bar
"""
import click

__all__ = ['DefaultGroup']
__version__ = '1.1'


class DefaultGroup(click.Group):
    """Invokes a subcommand marked with `default=True` if any subcommand not
    chosen.
    :param default_if_no_args: resolves to the default command if no arguments
                               passed.
    """

    def __init__(self, *args, **kwargs):
        self.default_cmd_name = None
        self.default_if_no_args = kwargs.pop('default_if_no_args', False)
        # To resolve as the default command.
        if not kwargs.get('ignore_unknown_options', True):
            raise ValueError('Default group accepts unknown options')
        self.ignore_unknown_options = True
        super(DefaultGroup, self).__init__(*args, **kwargs)

    def command(self, *args, **kwargs):
        default = kwargs.pop('default', False)
        decorator = super(DefaultGroup, self).command(*args, **kwargs)
        if not default:
            # Customized feature not used.
            return decorator

        def _decorator(f):
            cmd = decorator(f)
            if default:
                if self.default_cmd_name is not None:
                    del self.commands[cmd.name]
                    raise RuntimeError('Default command already defined')
                self.default_cmd_name = cmd.name
            return cmd
        return _decorator

    def parse_args(self, ctx, args):
        if not args and self.default_if_no_args:
            args.insert(0, self.default_cmd_name)
        return super(DefaultGroup, self).parse_args(ctx, args)

    def get_command(self, ctx, cmd_name):
        if cmd_name not in self.commands:
            # No command name matched.
            ctx.arg0 = cmd_name
            cmd_name = self.default_cmd_name
        return super(DefaultGroup, self).get_command(ctx, cmd_name)

    def resolve_command(self, ctx, args):
        base = super(DefaultGroup, self)
        cmd_name, cmd, args = base.resolve_command(ctx, args)
        if hasattr(ctx, 'arg0'):
            args.insert(0, ctx.arg0)
        return cmd_name, cmd, args

    def format_commands(self, ctx, formatter):
        formatter = DefaultCommandFormatter(self, formatter, mark='*')
        return super(DefaultGroup, self).format_commands(ctx, formatter)


class DefaultCommandFormatter(object):
    """Wraps a formatter to mark a default command."""

    def __init__(self, group, formatter, mark='*'):
        self.group = group
        self.formatter = formatter
        self.mark = mark

    def __getattr__(self, attr):
        return getattr(self.formatter, attr)

    def write_dl(self, rows, *args, **kwargs):
        rows_ = []
        for cmd_name, help in rows:
            if cmd_name == self.group.default_cmd_name:
                rows_.insert(0, (cmd_name + self.mark, help))
            else:
                rows_.append((cmd_name, help))
        return self.formatter.write_dl(rows_, *args, **kwargs)
