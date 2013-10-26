#!/bin/sh

# testing tcsh from @redstreet's argcopmlete issue
# https://github.com/kislyuk/argcomplete/issues/49 
export IFS=''
export COMP_LINE=${COMMAND_LINE}
export COMP_WORDBREAKS=
export COMP_POINT=${#COMMAND_LINE}
export _ARGCOMPLETE=1
tmuxp 8>&1 9>&2 1>/dev/null 2>/dev/null
