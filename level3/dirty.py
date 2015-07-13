import sys
from flask import Flask, request
import subprocess

app = Flask(__name__)
path = ""

def do(cmd):
    return subprocess.check_output(cmd, shell=True)


def success():
    return '{"success": true}', 200


@app.route("/healthcheck")
def health_check():
    return success()


@app.route("/isIndexed")
def is_indexed():
    return success()


@app.route("/index")
def index():
    # warm up cache
    global path
    path = request.args.get("path", "")
    do("(cd %s; git init; git add .); exit 0" % path)
    return success()


@app.route("/")
def query():
    q = request.args.get("q", "")
    results = do("(cd %s; git grep -nI --color=never %s); exit 0" % (path, q)).split("\n")
    stuff = []
    for line in results:
        if len(line) == 0:
            continue
        data = line.split(":")
        stuff.append('"%s:%s"' % (data[0].replace(path + "/", ""), data[1]))

    rtn = '{ "success": true, "results": ['
    rtn += ",".join(stuff)
    rtn += "] }"

    return rtn, 200


if __name__ == "__main__":
    if len(sys.argv) == 2:
        app.run(port=9090)