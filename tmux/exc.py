class SessionNotFound(Exception):
    pass

class SessionExists(Exception):
    pass

class NotRunning(Exception):
    '''
        class for when ._TMUX doesn't exist, this will cause an issue with
        building the workspace and running commands
    '''
    pass
