#!/usr/bin/env python

import os
import re
import sys
import time
import hashlib
import multiprocessing
from subprocess import Popen, PIPE

clone_spec = "lvl1-sptus5cu@stripe-ctf.com:level1"
clone_dir = "level1"
username = "user-lzjao7ro"


def get_file_contents(filename):
    fullpath = os.path.join(clone_dir, filename)
    return open(fullpath, "rb").read()


def put_file_contents(filename, data):
    fullpath = os.path.join(clone_dir, filename)
    open(fullpath, "wb").write(data)


def reset():
    print "resetting..."
    do(["git", "fetch", "origin", "master"])
    do(["git", "reset", "--hard", "origin/master"])


def do(cmd, stdin=None, stop_on_error=True, do_cwd=True):
    c =clone_dir if do_cwd else None
    p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, cwd=c)
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

    global clone_dir
    clone_dir = os.path.join(os.getcwd(), clone_dir)

    if os.path.isdir(clone_dir):
        print "Using existing repo at %s" % clone_dir
        reset()
    else:
        print "Cloning repo to %s" % clone_dir
        do(["git", "clone", clone_spec], do_cwd=False)


def prepare_index():
    print "preparing..."

    lines = get_file_contents("LEDGER.txt")

    def inc(m):
        a = int(m.group(1))
        return "%s: %d" % (username, a+1)

    (d, c) = re.subn("%s: (\d+)" % username, inc, lines)
    if c == 0:
        d += "%s: 1\n" % username

    put_file_contents("LEDGER.txt", d)

    do(["git", "add", "LEDGER.txt"])


def create_hash(content):
    data = "commit %d\0%s" % (len(content), content)
    return hashlib.sha1(data).hexdigest()


def worker_create(output, event, tree, parent, timestamp, start, step):
    print "worker_create (%d) running..." % start
    current = start
    while True:
        body = "tree %s\nparent %s\nauthor CTF user <sauerc@gmail.com> %s +0000\ncommitter CTF user <sauerc@gmail.com> %s +0000\n\nGive me a Gitcoin\n\n%d" % (tree, parent, timestamp, timestamp, current)
        output.put((body, create_hash(body)))
        current += step
        event.wait(0)
        if event.is_set():
            break
    print "worker_create (%d) exiting..." % start


def worker_test(test, queue, response, event, ident):
    print "worker_test (%d) running..." % ident
    while True:
        (data, sha1) = queue.get(True)
        if sha1 < test:
            response.put((data, sha1))
            event.set()
            break;
        event.wait(0)
        if event.is_set():
            break
    print "worker_test (%d) exiting..." % ident


def rt_solve():
    print "solving..."

    storage = multiprocessing.Queue()
    success = multiprocessing.Queue()
    event = multiprocessing.Event()

    target = get_file_contents("difficulty.txt")
    tree = do(["git", "write-tree"])
    parent = do(["git", "rev-parse", "HEAD"])
    timestamp = do(["date", "+%s"])

    create_count = 2
    test_count = 2
    children = []
    for t in xrange(create_count):
        p = multiprocessing.Process(target=worker_create,
                                    args=(storage,
                                          event,
                                          tree,
                                          parent,
                                          timestamp,
                                          t,
                                          create_count))
        p.start()
        children.append(p)

    for t in xrange(test_count):
        p = multiprocessing.Process(target=worker_test,
                                    args=(target,
                                          storage,
                                          success,
                                          event,
                                          t))
        p.start()
        children.append(p)

    (data, sha1) = success.get()
    event.set()
    print ""
    print "Mined a Gitcoin with commit: %s" % sha1
    do(["git", "hash-object", "-t", "commit", "--stdin", "-w"], data)
    do(["git", "reset", "--hard", sha1])


def main():
    clone()

    while True:
        prepare_index()
        rt_solve()
        if do(["git", "push", "origin", "master"]) is not False:
            print "Success :)"
            return 0
        else:
            print "Starting over :("
            reset()

    return 1


if __name__ == "__main__":
    sys.exit(main())
