import subprocess
import sys


plugin_paths = [
    "plugins/tmuxp_plugin_one",
    "plugins/tmuxp_plugin_two"
]


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def install_plugins():
    for plugin in plugin_paths:
        install(plugin)


if __name__ == "__main__":
    install_plugins()
