import os


def curjoin(_file):  # return filepath relative to __file__ (this file)
    return os.path.join(os.path.dirname(__file__), _file)


def loadfixture(_file):  # return fixture data, relative to __file__
    return open(curjoin(_file)).read()
