#!/usr/bin/env bash

clear
./killthem.sh
python ./level4.py -l /tmp/level4/node1/node1.sock -d /tmp/level4/node1 -local &
sleep 1
python ./level4.py -l /tmp/level4/node2/node2.sock -d /tmp/level4/node2 --join=/tmp/level4/node1/node1.sock -local