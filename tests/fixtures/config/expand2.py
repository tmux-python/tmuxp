import os


def curjoin(_file):  # return filepath relative to __file__ (this file)
    return os.path.join(os.path.dirname(__file__), _file)

unexpanded_yaml = open(curjoin('expand2-unexpanded.yaml')).read()
expanded_yaml = open(curjoin('expand2-expanded.yaml')).read().format(
    HOME=os.path.expanduser('~')
)
