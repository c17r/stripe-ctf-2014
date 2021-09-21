#!/usr/bin/env bash

ps | grep -e "[l]evel3" -e "[d]irty" | cut -d ' ' -f1 | xargs kill
