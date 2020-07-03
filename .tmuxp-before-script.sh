#!/bin/sh
poetry shell --no-ansi --no-interaction &2> /dev/null
poetry install --no-ansi --no-interaction &2> /dev/null
