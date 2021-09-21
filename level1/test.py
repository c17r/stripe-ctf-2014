#!/usr/bin/env python

import sys
import time
import multiprocessing

def worker(e):
    print "worker start"
    while True:
        e.wait(0)
        print e.is_set()
        if e.is_set():
            return
    print "worker end"


def main():
    print "main start"
    e = multiprocessing.Event()
    p = multiprocessing.Process(target=worker, args=(e,))

    p.start()
    print "sleep"
    time.sleep(1)
    print "awake"

    e.set()
    print "main end"


if __name__ == "__main__":
    sys.exit(main())