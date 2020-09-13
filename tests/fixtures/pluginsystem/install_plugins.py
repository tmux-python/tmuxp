import subprocess
import sys


plugin_paths = [
    "plugins/tmuxp_test_plugin_bwb",
    "plugins/tmuxp_test_plugin_bs",
    "plugins/tmuxp_test_plugin_r",
    "plugins/tmuxp_test_plugin_owc",
    "plugins/tmuxp_test_plugin_awf",
]


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    

def install_plugins():
    for plugin in plugin_paths:
        install(plugin)


if __name__ == "__main__":
    install_plugins()
