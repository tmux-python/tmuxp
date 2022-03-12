import os

from .._util import load_fixture

unexpanded_yaml = load_fixture("config/expand2-unexpanded.yaml")
expanded_yaml = load_fixture("config/expand2-expanded.yaml").format(
    HOME=os.path.expanduser("~")
)
