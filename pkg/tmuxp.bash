#!/usr/bin/env bash

_python_argcomplete() {
    local IFS='\013'
    COMPREPLY=( $(IFS="$IFS" \
                  COMP_LINE="$COMP_LINE" \
                  COMP_POINT="$COMP_POINT" \
                  _ARGCOMPLETE_COMP_WORDBREAKS="$COMP_WORDBREAKS" \
                  _ARGCOMPLETE=1 \
                  "$1" 8>&1 9>&2 1>/dev/null 2>/dev/null) )
    if [[ $? != 0 ]]; then
        unset COMPREPLY
    fi
}



# SHELLNAME=`lsof -p $$ | awk '(NR==2) {print $1}'`

# if [ $SHELLNAME = "bash" ]; then
# elif [ $SHELLNAME = "zsh" ]; then
# elif [ $SHELLNAME = "tcsh" ];  then
# fi

eval "$(register-python-argcomplete tmuxp)"
