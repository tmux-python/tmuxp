import os

config_unexpanded = {  # shell_command_before is string in some areas
    'session_name': 'sampleconfig',
    'start_directory': '/',
    'windows': [
        {
            'window_name': 'editor',
            'start_directory': '~',
            'shell_command_before': 'source .venv/bin/activate',
            'panes': [
                {'shell_command': ['vim']},
                {
                    'shell_command_before': ['rbenv local 2.0.0-p0'],
                    'shell_command': ['cowsay "hey"'],
                },
            ],
            'layout': 'main-verticle',
        },
        {
            'shell_command_before': 'rbenv local 2.0.0-p0',
            'window_name': 'logging',
            'panes': [{'shell_command': ['tail -F /var/log/syslog']}, {}],
        },
        {
            'window_name': 'shufu',
            'panes': [
                {
                    'shell_command_before': ['rbenv local 2.0.0-p0'],
                    'shell_command': ['htop'],
                }
            ],
        },
        {'options': {'automatic-rename': True}, 'panes': [{'shell_command': ['htop']}]},
        {'panes': ['top']},
    ],
}

config_expanded = {  # shell_command_before is string in some areas
    'session_name': 'sampleconfig',
    'start_directory': '/',
    'windows': [
        {
            'window_name': 'editor',
            'start_directory': os.path.expanduser('~'),
            'shell_command_before': ['source .venv/bin/activate'],
            'panes': [
                {'shell_command': ['vim']},
                {
                    'shell_command_before': ['rbenv local 2.0.0-p0'],
                    'shell_command': ['cowsay "hey"'],
                },
            ],
            'layout': 'main-verticle',
        },
        {
            'shell_command_before': ['rbenv local 2.0.0-p0'],
            'window_name': 'logging',
            'panes': [
                {'shell_command': ['tail -F /var/log/syslog']},
                {'shell_command': []},
            ],
        },
        {
            'window_name': 'shufu',
            'panes': [
                {
                    'shell_command_before': ['rbenv local 2.0.0-p0'],
                    'shell_command': ['htop'],
                }
            ],
        },
        {'options': {'automatic-rename': True}, 'panes': [{'shell_command': ['htop']}]},
        {'panes': [{'shell_command': ['top']}]},
    ],
}

config_after = {  # shell_command_before is string in some areas
    'session_name': 'sampleconfig',
    'start_directory': '/',
    'windows': [
        {
            'window_name': 'editor',
            'start_directory': os.path.expanduser('~'),
            'shell_command_before': ['source .venv/bin/activate'],
            'panes': [
                {'shell_command': ['source .venv/bin/activate', 'vim']},
                {
                    'shell_command_before': ['rbenv local 2.0.0-p0'],
                    'shell_command': [
                        'source .venv/bin/activate',
                        'rbenv local 2.0.0-p0',
                        'cowsay "hey"',
                    ],
                },
            ],
            'layout': 'main-verticle',
        },
        {
            'shell_command_before': ['rbenv local 2.0.0-p0'],
            'start_directory': '/',
            'window_name': 'logging',
            'panes': [
                {'shell_command': ['rbenv local 2.0.0-p0', 'tail -F /var/log/syslog']},
                {'shell_command': ['rbenv local 2.0.0-p0']},
            ],
        },
        {
            'start_directory': '/',
            'window_name': 'shufu',
            'panes': [
                {
                    'shell_command_before': ['rbenv local 2.0.0-p0'],
                    'shell_command': ['rbenv local 2.0.0-p0', 'htop'],
                }
            ],
        },
        {
            'start_directory': '/',
            'options': {'automatic-rename': True},
            'panes': [{'shell_command': ['htop']}],
        },
        {'start_directory': '/', 'panes': [{'shell_command': ['top']}]},
    ],
}
