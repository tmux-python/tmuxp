#!/bin/sh


echoerr() { echo "$@" 1>&2; }
echoerr An error has occurred

exit 113   # Will return 113 to shell.
           # To verify this, type "echo $?" after script terminates.
