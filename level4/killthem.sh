#!/usr/bin/env bash

ps | egrep -e "[l]evel4.py" -e "[o]ctopus" -e "[s]qlcluster" | awk '{print $1}' | xargs kill -9
