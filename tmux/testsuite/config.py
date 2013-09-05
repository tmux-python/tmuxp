import os
import shutil
import kaptan
import unittest


TMUXWRAPPER_DIR = os.path.join(os.path.dirname(__file__), '.tmuxwrapper')

sampleconfigdict = {
    'name': 'sampleconfig',
    'windows': [{
        'window_name': 'editor',
        'panes': [
            {
                'start_directory': '~', 'shell_command': ['vim'],
                },  {
                'shell_command': ['cowsay "hey"']
            },
        ],
        'layout': 'main-verticle'},
        {
            'window_name': 'logging',
            'panes': [
                {'shell_command': ['tail -F /var/log/syslog']}
            ]
        },
        {
            'automatic_rename': True,
            'panes': [
                {'shell_command': 'htop'}
            ]
        }]
}

sampleconfigexpanded = {
    'name':
    'sampleconfig',
    'windows':
    {
        'editor': {
            'panes': [
                {
                    'cmd': ['vim', 'cowsay "hey"']
                }
            ],
            'layout': 'main-verticle'
        },
        'logs': 'tail -F /var/log/syslog',
        'server': 'htop'
    }
}


class ConfigTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # run parent
        # setUpClass
        if not os.path.exists(TMUXWRAPPER_DIR):
            os.makedirs(
                TMUXWRAPPER_DIR)
            # super(ConfigTest, cls).setUpClass()

    def test_export_json(self):
        json_config_file = os.path.join(TMUXWRAPPER_DIR, 'config.json')

        config = kaptan.Kaptan()
        config.import_config(sampleconfigdict)

        json_config_data = config.export('json', indent=2)

        buf = open(json_config_file, 'w')
        buf.write(json_config_data)
        buf.close()

        new_config = kaptan.Kaptan()
        new_config_data = new_config.import_config(json_config_file).get()
        self.assertDictEqual(sampleconfigdict, new_config_data)

    def test_export_yaml(self):
        yaml_config_file = os.path.join(TMUXWRAPPER_DIR, 'config.yaml')

        config = kaptan.Kaptan()
        config.import_config(sampleconfigdict)

        yaml_config_data = config.export('yaml', indent=2)

        buf = open(yaml_config_file, 'w')
        buf.write(yaml_config_data)
        buf.close()

        new_config = kaptan.Kaptan()
        new_config_data = new_config.import_config(yaml_config_file).get()
        self.assertDictEqual(sampleconfigdict, new_config_data)

    def test_scan_config(self):
        configs = []

        garbage_file = os.path.join(TMUXWRAPPER_DIR, 'config.psd')
        buf = open(garbage_file, 'w')
        buf.write('wat')
        buf.close()

        if os.path.exists(TMUXWRAPPER_DIR):
            for r, d, f in os.walk(TMUXWRAPPER_DIR):
                for filela in (x for x in f if x.endswith(('.json', '.ini', 'yaml'))):
                    configs.append(os.path.join(
                        TMUXWRAPPER_DIR, filela))

        files = 0
        if os.path.exists(os.path.join(TMUXWRAPPER_DIR, 'config.json')):
            files += 1
            self.assertIn(os.path.join(
                TMUXWRAPPER_DIR, 'config.json'), configs)

        if os.path.exists(os.path.join(TMUXWRAPPER_DIR, 'config.yaml')):
            files += 1
            self.assertIn(os.path.join(
                TMUXWRAPPER_DIR, 'config.yaml'), configs)

        if os.path.exists(os.path.join(TMUXWRAPPER_DIR, 'config.ini')):
            files += 1
            self.assertIn(os.path.join(TMUXWRAPPER_DIR, 'config.ini'), configs)

        self.assertEqual(len(configs), files)

    @classmethod
    def tearDownClass(cls):
        return
    if shutil.rmtree(TMUXWRAPPER_DIR):
        os.makedirs(
            TMUXWRAPPER_DIR)


class ConfigTestExpand(unittest.TestCase):

    def test_expand_windows(self):
        windows = sampleconfigdict['windows']
        print(windows)

        # if isinstance(windows, dict):
        #    windows = [expand_window(window, window_name) for window_name, window in windows.iteritems()]
        # else:
        #    windows = [expand_window(windows) for window in windows]

        # for window_name, window in windows:
        #    self.assertIn('panes', window)

    pass


def expand_window(window, window_name=None):
    """expand the window dictionary into full form

    window
    string or list. window data. expanded into cmd's
    window_name
    if the vanilla configuration dict used a name key for each window, like

        editing:
            - vim
            - htop
            - ipython

        running .iteritems() on the array of [windows] will allow us to pass
        it in like:

        [expand_window(window, window_name) for window_name, window in windows.iteritems()]
        """

    # the config is listing the window with window_name as the key
    #   window_name:
    #       - cmd
    #   we will make it
    #   - name: window_name
    #     panes:
    #       cmd: [cmd]
    #     attributes
    if isinstance(window, basestring) and window_name:
        # window is using short form
        # window_name: cmd
        # make it into window_name: { cmd: ['cmd'] }
        window = {
            'name':
            window_name
        }

        if not 'panes' in window:

            'panes' [
                'cmd': [window]
            ]

    if 'window_name' in window:
        pass
    elif 'window_name' not in window and window_name:
        window['window_name'] = window_name
    elif 'window_name' not in window and window_name is None:
        window['window']

    # if len(window) == int(1)
    # isinstance(window, basestring):
    """expand
    window[name] = 'command'

        to

        window[name] = {
        panes=['command']
        }
        """
    if isinstance(window, basestring):
        windowoptions = dict(
            panes=[window[name]]
        )
    else:
        windowoptions = window[name]

    window = dict(name=name, **windowoptions)
    if len(window['panes']) > int(1):
        pass

    return window
