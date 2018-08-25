from .._util import loadfixture

teamocil_yaml = loadfixture('config_teamocil/test1.yaml')
teamocil_conf = {
    'windows': [
        {
            'name': 'sample-two-panes',
            'root': '~/Code/sample/www',
            'layout': 'even-horizontal',
            'panes': [{'cmd': ['pwd', 'ls -la']}, {'cmd': 'rails server --port 3000'}],
        }
    ]
}

expected = {
    'session_name': None,
    'windows': [
        {
            'window_name': 'sample-two-panes',
            'layout': 'even-horizontal',
            'start_directory': '~/Code/sample/www',
            'panes': [
                {'shell_command': ['pwd', 'ls -la']},
                {'shell_command': 'rails server --port 3000'},
            ],
        }
    ],
}
