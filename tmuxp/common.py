
class EnvironmentMixin(object):

    """Mixin class for managing session and server level environment
    variables in tmux.

    """

    _add_option = None

    def __init__(self, add_option=None):
        self._add_option = add_option
    
    def set_environment(self, name, value):
        """Set environment ``$ tmux set-environment <name> <value>``.

        :param name: the environment variable name. such as 'PATH'.
        :type option: string
        :param value: environment value.
        :type value: string

        """

        args = ['set-environment']
        if self._add_option:
            args += [self._add_option]

        args += [name, value]
            
        proc = self.cmd(*args)

        if proc.stderr:
            if isinstance(proc.stderr, list) and len(proc.stderr) == int(1):
                proc.stderr = proc.stderr[0]
            raise ValueError('tmux set-environment stderr: %s' % proc.stderr)

    def unset_environment(self, name):
        """Unset environment variable ``$ tmux set-environment -u <name>``.

        :param name: the environment variable name. such as 'PATH'.
        :type option: string
        """

        args = ['set-environment']
        if self._add_option:
            args += [self._add_option]
        args += ['-u', name]
            
        proc = self.cmd(*args)

        if proc.stderr:
            if isinstance(proc.stderr, list) and len(proc.stderr) == int(1):
                proc.stderr = proc.stderr[0]
            raise ValueError('tmux set-environment stderr: %s' % proc.stderr)

    def remove_environment(self, name):
        """Remove environment variable ``$ tmux set-environment -r <name>``.

        :param name: the environment variable name. such as 'PATH'.
        :type option: string
        """

        args = ['set-environment']
        if self._add_option:
            args += [self._add_option]
        args += ['-r', name]
            
        proc = self.cmd(*args)

        if proc.stderr:
            if isinstance(proc.stderr, list) and len(proc.stderr) == int(1):
                proc.stderr = proc.stderr[0]
            raise ValueError('tmux set-environment stderr: %s' % proc.stderr)

    def show_environment(self, name=None):
        """Show environment ``$tmux show-environment -t [session] <name>``.

        Return dict of environment variables for the session or the value of a
        specific variable if the name is specified.

        :param name: the environment variable name. such as 'PATH'.
        :type option: string
        """
        tmux_args = ['show-environment']
        if self._add_option:
            tmux_args += [self._add_option]
        if name:
            tmux_args += [name]
        vars = self.cmd(*tmux_args).stdout
        vars = [tuple(item.split('=', 1)) for item in vars]
        vars_dict = {}
        for t in vars:
            if len(t) == 2:
                vars_dict[t[0]] = t[1]
            elif len(t) == 1:
                vars_dict[t[0]] = True
            else:
                raise ValueError('unexpected variable %s', t)

        if name:
            return vars_dict.get(name)

        return vars_dict
