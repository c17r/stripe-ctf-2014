#!/usr/bin/env python

import os
import re
import sys
import time
import hashlib
import threading
from subprocess import Popen, PIPE

clone_spec = "lvl1-sptus5cu@stripe-ctf.com:level1"
clone_dir = "level1"
username = "user-lzjao7ro"


def get_file_contents(path, filename):
    fullpath = os.path.join(path, filename)
    return open(fullpath, "rb").read()

def do(cmd, path=None, stdin=None, stop_on_error=True):
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=path)
    (stdout, stderr) = p.communicate(stdin)
    if p.returncode != 0:
        if stop_on_error:
            print stdout
            print stderr
            sys.exit(1)
        return False
    elif stderr:
        return stderr
    else:
        return stdout.rstrip()


def clone():
    print "cloning..."
    path = os.path.join(os.getcwd(), clone_dir)
    if os.path.isdir(path):
        print "Using existing repo at %s" % path
        reset(path)
    else:
        print "Cloning repo to %s" % path
        do(["git", "clone", clone_spec, path])

    return path


def prepare_index(path):
    print "preparing..."
    ledger = os.path.join(path, "LEDGER.txt")

    lines = open(ledger, "rb").read()

    def inc(m):
        a = int(m.group(1))
        return "%s: %d" % (username, a+1)

    (d, c) = re.subn("%s: (\d+)" % username, inc, lines)
    if c == 0:
        d += "%s: 1\n" % username

    open(ledger, "wb").write(d)

    do(["git", "add", "LEDGER.txt"], path)


def solve(path, start, step):
    print "solving..."
    target = get_file_contents(path, "difficulty.txt")

    tree = do(["git", "write-tree"], path)
    parent = do(["git", "rev-parse", "HEAD"], path)
    timestamp = do(["date", "+%s"])

    current = start

    def create_hash(content):
        header = "commit %d\0" % len(content)
        store = header + content
        return hashlib.sha1(store).hexdigest()

    def show_count():
        print "start: %d - current %d" % (start, current)
        print "speed: %d" % (current/10.0)

    t = threading.Timer(10.0, show_count)
    t.start()

    while True:

        body = "tree %s\nparent %s\nauthor CTF user <sauerc@gmail.com> %s +0000\ncommitter CTF user <sauerc@gmail.com> %s +0000\n\nGive me a Gitcoin\n\n%d" % (tree, parent, timestamp, timestamp, current)

        #sha1 = do(["git", "hash-object", "-t", "commit", "--stdin"], path, body)
        sha1 = create_hash(body)

        if sha1 < target:
            print ""
            print "Mined a Gitcoin with commit: %s" % sha1
            do(["git", "hash-object", "-t", "commit", "--stdin", "-w"], path, body)
            do(["git", "reset", "--hard", sha1], path)
            return

        current += step

def reset(path):
    print "resetting..."
    do(["git", "fetch", "origin", "master"], path)
    do(["git", "reset", "--hard", "origin/master"], path)


def main():
    path = clone()

    while True:
        prepare_index(path)
        solve(path, 1, 1)
        if do(["git", "push", "origin", "master"], path) is not False:
            print "Success :)"
            return 0
        else:
            print "Starting over :("
            reset(path)

    return 1


if __name__ == "__main__":
    sys.exit(main())
