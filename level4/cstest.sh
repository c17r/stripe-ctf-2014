#!/usr/bin/env bash

LOC=`pwd`

run() {
    curl-unix-socket -d "$@" unix:///tmp/level4/node2/node2.sock:/sql
}

setup() {
    mkdir -p /tmp/level4/node1
    mkdir -p /tmp/level4/node2
    mkdir -p /tmp/level4/node3
    mkdir -p /tmp/level4/node4
    mkdir -p /tmp/level4/node5

    rm -rf /tmp/level4/node1/*.*
    rm -rf /tmp/level4/node2/*.*
    rm -rf /tmp/level4/node3/*.*
    rm -rf /tmp/level4/node4/*.*
    rm -rf /tmp/level4/node5/*.*

    python ./level4.py -l /tmp/level4/node1/node1.sock -d /tmp/level4/node1 -local &
    python ./level4.py -l /tmp/level4/node2/node2.sock -d /tmp/level4/node2 --join=/tmp/level4/node1/node1.sock -local &
    python ./level4.py -l /tmp/level4/node3/node3.sock -d /tmp/level4/node3 --join=/tmp/level4/node1/node1.sock -local &
    python ./level4.py -l /tmp/level4/node4/node4.sock -d /tmp/level4/node4 --join=/tmp/level4/node1/node1.sock -local &
    python ./level4.py -l /tmp/level4/node5/node5.sock -d /tmp/level4/node5 --join=/tmp/level4/node1/node1.sock -local &
}

cleanup() {
    ps | grep "[l]evel4" | awk '{print $1}' | xargs kill
}

cleanup

setup

run "CREATE TABLE hello (world int);INSERT INTO hello(world) VALUES (3), (4)"
run "INSERT INTO hello (world) VALUES (1), (2)"
run "SELECT * FROM hello"
