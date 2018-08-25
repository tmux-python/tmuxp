from .._util import loadfixture

teamocil_yaml = loadfixture('config_teamocil/layouts.yaml')

teamocil_dict = {
    'two-windows': {
        'windows': [
            {
                'name': 'foo',
                'clear': True,
                'root': '/foo',
                'layout': 'tiled',
                'panes': [{'cmd': "echo 'foo'"}, {'cmd': "echo 'foo again'"}],
            },
            {
                'name': 'bar',
                'root': '/bar',
                'splits': [
                    {
                        'cmd': ["echo 'bar'", "echo 'bar in an array'"],
                        'target': 'bottom-right',
                    },
                    {'cmd': "echo 'bar again'", 'focus': True, 'width': 50},
                ],
            },
        ]
    },
    'two-windows-with-filters': {
        'windows': [
            {
                'name': 'foo',
                'root': '/foo',
                'filters': {
                    'before': ['echo first before filter', 'echo second before filter'],
                    'after': ['echo first after filter', 'echo second after filter'],
                },
                'panes': [
                    {'cmd': "echo 'foo'"},
                    {'cmd': "echo 'foo again'", 'width': 50},
                ],
            }
        ]
    },
    'two-windows-with-custom-command-options': {
        'windows': [
            {
                'name': 'foo',
                'cmd_separator': '\n',
                'with_env_var': False,
                'clear': True,
                'root': '/foo',
                'layout': 'tiled',
                'panes': [{'cmd': "echo 'foo'"}, {'cmd': "echo 'foo again'"}],
            },
            {
                'name': 'bar',
                'cmd_separator': ' && ',
                'with_env_var': True,
                'root': '/bar',
                'splits': [
                    {
                        'cmd': ["echo 'bar'", "echo 'bar in an array'"],
                        'target': 'bottom-right',
                    },
                    {'cmd': "echo 'bar again'", 'focus': True, 'width': 50},
                ],
            },
        ]
    },
    'three-windows-within-a-session': {
        'session': {
            'name': 'my awesome session',
            'windows': [
                {'name': 'first window', 'panes': [{'cmd': "echo 'foo'"}]},
                {'name': 'second window', 'panes': [{'cmd': "echo 'foo'"}]},
                {'name': 'third window', 'panes': [{'cmd': "echo 'foo'"}]},
            ],
        }
    },
}


two_windows = {
    'session_name': None,
    'windows': [
        {
            'window_name': 'foo',
            'start_directory': '/foo',
            'clear': True,
            'layout': 'tiled',
            'panes': [
                {'shell_command': "echo 'foo'"},
                {'shell_command': "echo 'foo again'"},
            ],
        },
        {
            'window_name': 'bar',
            'start_directory': '/bar',
            'panes': [
                {
                    'shell_command': ["echo 'bar'", "echo 'bar in an array'"],
                    'target': 'bottom-right',
                },
                {'shell_command': "echo 'bar again'", 'focus': True},
            ],
        },
    ],
}

two_windows_with_filters = {
    'session_name': None,
    'windows': [
        {
            'window_name': 'foo',
            'start_directory': '/foo',
            'shell_command_before': [
                'echo first before filter',
                'echo second before filter',
            ],
            'shell_command_after': [
                'echo first after filter',
                'echo second after filter',
            ],
            'panes': [
                {'shell_command': "echo 'foo'"},
                {'shell_command': "echo 'foo again'"},
            ],
        }
    ],
}

two_windows_with_custom_command_options = {
    'session_name': None,
    'windows': [
        {
            'window_name': 'foo',
            'start_directory': '/foo',
            'clear': True,
            'layout': 'tiled',
            'panes': [
                {'shell_command': "echo 'foo'"},
                {'shell_command': "echo 'foo again'"},
            ],
        },
        {
            'window_name': 'bar',
            'start_directory': '/bar',
            'panes': [
                {
                    'shell_command': ["echo 'bar'", "echo 'bar in an array'"],
                    'target': 'bottom-right',
                },
                {'shell_command': "echo 'bar again'", 'focus': True},
            ],
        },
    ],
}

three_windows_within_a_session = {
    'session_name': 'my awesome session',
    'windows': [
        {'window_name': 'first window', 'panes': [{'shell_command': "echo 'foo'"}]},
        {'window_name': 'second window', 'panes': [{'shell_command': "echo 'foo'"}]},
        {'window_name': 'third window', 'panes': [{'shell_command': "echo 'foo'"}]},
    ],
}
