#!/usr/bin/env python
import os
import sys
import time
import shutil
import argparse
import traceback
import tempfile
import logging
import Server

logging.basicConfig(level=logging.DEBUG)


def get_cmd_args():
    parser = argparse.ArgumentParser(description="Server Some SQL")
    parser.add_argument('-v', action='store_true', dest='verbose')
    parser.add_argument('-l', required=True, dest='server')
    parser.add_argument('--join', dest='join')
    parser.add_argument('-d', required=True, dest='directory')
    parser.add_argument('-local', action='store_true', dest='local')
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    return args.server, args.directory, args.join, args.local


def sleep_for_network():
    while True:
        logging.debug("Waiting for files.")
        _, _, files = next(os.walk("."))
        if len(files) == 4:
            break
        time.sleep(0.1)


def main():
    address, directory, join, local = get_cmd_args()

    if directory == "":
        directory = tempfile.mkdtemp("node")
    else:
        if not os.path.exists(directory):
            os.makedirs(directory, 0755)

    old_cwd = os.getcwd()
    os.chdir(directory)

    if not local:
        sleep_for_network()

    s = Server.Server(directory, address)

    try:
        s.listen_and_serve(join)
    except Exception as e1:
        logging.exception("level4.main")
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(directory)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e2:
        logging.exception("level4.__main__")
