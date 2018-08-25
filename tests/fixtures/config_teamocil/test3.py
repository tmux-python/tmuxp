from .._util import loadfixture

teamocil_yaml = loadfixture('config_teamocil/test3.yaml')

teamocil_dict = {
    'windows': [
        {
            'name': 'my-first-window',
            'root': '~/Projects/foo-www',
            'layout': 'even-vertical',
            'filters': {
                'before': 'rbenv local 2.0.0-p0',
                'after': 'echo \'I am done initializing this pane.\'',
            },
            'panes': [
                {'cmd': 'git status'},
                {'cmd': 'bundle exec rails server --port 40', 'focus': True},
                {'cmd': ['sudo service memcached start', 'sudo service mongodb start']},
            ],
        }
    ]
}

expected = {
    'session_name': None,
    'windows': [
        {
            'window_name': 'my-first-window',
            'layout': 'even-vertical',
            'start_directory': "~/Projects/foo-www",
            'shell_command_before': 'rbenv local 2.0.0-p0',
            'shell_command_after': ('echo ' '\'I am done initializing this pane.\''),
            'panes': [
                {'shell_command': 'git status'},
                {'shell_command': 'bundle exec rails server --port 40', 'focus': True},
                {
                    'shell_command': [
                        'sudo service memcached start',
                        'sudo service mongodb start',
                    ]
                },
            ],
        }
    ],
}
