# -*- coding: utf8 - *-
"""
    tmuxp.window
    ~~~~~~~~~~~~

    tmuxp helps you manage tmux workspaces.

    :copyright: Copyright 2013 Tony Narlock.
    :license: BSD, see LICENSE for details
"""
import pipes
from .util import TmuxObject
from .pane import Pane
from .formats import PANE_FORMATS
from .logxtreme import logging


class Window(TmuxObject):
    '''
    ``tmux(1) window``.
    '''

    def __init__(self, session=None, **kwargs):
        self._panes = list()  # list of panes

        if not session:
            raise ValueError(
                "Window requires a Session object by "
                "specifying session=Session"
            )
        self.session = session
        self.server = self.session.server

        self._TMUX = {}
        self.update(**kwargs)

    def __repr__(self):
        return "%s(%s %s:%s, %s)" % (
            self.__class__.__name__,
            self.get('window_id'),
            self.get('window_index'),
            self.get('window_name'),  # @todo, bug when window name blank
            self.session
        )

    def tmux(self, *args, **kwargs):
        #if '-t' not in kwargs:
        #    kwargs['-t'] = self.get['session_id']
        return self.server.tmux(*args, **kwargs)

    def select_layout(self, layout=None):
        '''
        wrapper for ``tmux(1)``::

            $ tmux select-layout <layout>

        The following layouts are supported::

            even-horizontal
                Panes are spread out evenly from left to right across the
                window.

            even-vertical
                Panes are spread evenly from top to bottom.

            main-horizontal
                A large (main) pane is shown at the top of the window and the
                remaining panes are spread from left to right in the leftover
                space at the bottom.  Use the main-pane-height window option to
                specify the height of the top pane.

            main-vertical
                Similar to main-horizontal but the large pane is placed on the
                left and the others spread from top to bottom along the right.
                See the main-pane-width window option.

            tiled
                Panes are spread out as evenly as possible over the window in
                both rows and columns.

            In addition, select-layout may be used to apply a previously used
            layout - the list-windows command displays the layout of each
            window in a form suitable for use with select-layout. For example::

                $ tmux list-windows
                0: ksh [159x48]
                    layout: bb62,159x48,0,0{79x48,0,0,79x48,80,0}
                $ tmux select-layout bb62,159x48,0,0{79x48,0,0,79x48,80,0}

        :param layout: string of the layout, 'even-horizontal', 'tiled', etc.
        :type layout: string
        '''
        self.tmux(
            'select-layout',
            '-t%s' % self.target,      # target (name of session)
            layout
        )

    @property
    def target(self):
        return "%s:%s" % (self.session.get('session_id'), self.get('window_id'))

    def set_window_option(self, option, value):
        '''
        wrapper for ``tmux(1)``::

            $ tmux set-window-option <option> <value>

        :param option: the window option. such as 'automatic_rename'.
        :type option: string

        :param value: window value. True/False will turn in 'on' and 'off'.
        :type value: string or bool
        '''

        if value:
            value = 'on'
        else:
            value = 'off'

        self.tmux(
            'set-window-option', option, value
        )

    def rename_window(self, new_name):
        '''rename window and return new window object::

            $ tmux rename-window <new_name>

        :param new_name: name of the window
        :type new_name: string
        '''
        try:
            self.tmux(
                'rename-window',
                '-t%s' % self.target,
                pipes.quote(new_name)
            )
            self['window_name'] = new_name
        except Exception, e:
            logging.error(e)

        self.session.list_windows()

        return self

    def select_pane(self, target_pane):
        '''
            ``$ tmux select-pane``

        Returns :class:`Pane`.

        :param target_pane: ``target_pane``, or ``-U``,``-D``, ``-L``, ``-R``.
        :type target_pane: string

        Todo: make 'up', 'down', 'left', 'right' acceptable ``target_pane``.
        '''
        if isinstance(target_pane, basestring) and not ':' not in target_pane or isinstance(target_pane, int):
            target_pane = "%s.%s" % (self.target, target_pane)

        try:
            self.tmux('select-pane', '-t', target_pane)
        except Exception:
            logging.error('pane not found %s %s' % (target_pane, self.list_panes()))
        self.list_panes()
        return self.attached_pane()

    def split_window(self, *args, **kwargs):
        '''
        Splits window. Returns the created :class:`Pane`.

        Used for splitting window and holding in a python object.

        Iterates ``$ tmux split-window``, ``-P`` to return data and
        ``-F`` for return formatting.

        Arguments may be passed through same as ``$ tmux split-window``.

        -h
            horizontal
        -v
            vertical
        '''

        formats = ['session_name', 'session_id', 'window_index', 'window_id'] + PANE_FORMATS
        tmux_formats = ['#{%s}\t' % format for format in formats]

        pane = self.tmux(
            'split-window',
            '-P', '-F%s' % ''.join(tmux_formats),     # output
        )

        # zip and map the results into the dict of formats used above
        pane = dict(zip(formats, pane.split('\t')))

        # clear up empty dict
        pane = dict((k, v) for k, v in pane.iteritems() if v)
        pane = Pane(window=self, **pane)
        self._panes.append(pane)
        self.list_panes()  # refresh all panes in :class:`Window`

        return pane

    def attached_pane(self):
        '''
        returns the attached :class:`Pane`.
        '''
        panes = self.list_panes()

        for pane in panes:
            if 'pane_active' in pane:
                # for now pane_active is a unicode
                if pane.get('pane_active') == '1':
                    return pane
                else:
                    continue

        return False

    def list_panes(self):
        '''
            Returns a list of :class:`Pane` for the window.
        '''
        formats = ['session_name', 'session_id', 'window_index', 'window_id'] + PANE_FORMATS
        tmux_formats = ['#{%s}\t' % format for format in formats]

        #if isinstance(self.get('window_id'), basestring):
        #    window_id =

        panes = self.tmux(
            'list-panes',
            #'-s',                               # for sessions
            #'-t%s' % self._session.session_name,      # target (name of session)
            '-t%s' % self.get('window_index'),      # target (name of session)
            '-F%s' % ''.join(tmux_formats),     # output
            _iter=True                          # iterate line by line
        )

        # zip and map the results into the dict of formats used above
        panes = [dict(zip(formats, pane.split('\t'))) for pane in panes]

        # clear up empty dict
        panes = [
            dict((k, v) for k, v in pane.iteritems() if v) for pane in panes
        ]

        # filter by window_index
        panes = [
            pane for pane in panes if pane['window_index'] == self.get('window_index')
        ]

        new_panes = panes

        if not self._panes:
            for pane in new_panes:
                logging.debug('adding pane_id %s for window_id %s' % (pane['pane_id'], pane['window_id']))
                self._panes.append(Pane(window=self, **pane))
            return self._panes

        new = {pane['pane_id']: pane for pane in new_panes}
        old = {pane.get('pane_id'): pane for pane in self._panes}

        created = set(new.keys()) - set(old.keys()) or ()
        deleted = set(old.keys()) - set(new.keys()) or ()
        intersect = set(new.keys()).intersection(set(old.keys()))

        diff = {id: dict(set(new[id].items()) - set(old[id].items())) for id in intersect}

        intersect = set(k for k, v in diff.iteritems() if v) or ()
        diff = dict((k, v) for k, v in diff.iteritems() if v) or ()

        if diff or created or deleted:
            log_diff = "sync sessions for server:\n"
        else:
            log_diff = None
        if diff and intersect:
            log_diff += "diff %s for %s" % (diff, intersect)
        if created:
            log_diff += "created %s" % created
        if deleted:
            log_diff += "deleted %s" % deleted
        if log_diff:
            logging.info(log_diff)

        for p in self._panes:
            # remove pane objects if deleted or out of session
            if p.get('pane_id') in deleted or self.get('session_id') != p.get('session_id'):
                logging.debug("removing %s" % p)
                self._panes.remove(p)

            if p.get('pane_id') in intersect and p.get('p_id') in diff:
                logging.debug('updating pane_id %s window_id %s' % (p.get('pane_id'), p.get('window_id')))
                p.update(diff[p.get('pane_id')])

        # create pane objects for non-existant pane_id's
        for pane in [new[pane_id] for pane_id in created]:
            logging.debug('adding pane_id %s window_id %s' % (pane['pane_id'], pane['window_id']))
            self._panes.append(Pane(window=self, **pane))

        return self._panes
