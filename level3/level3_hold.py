import re
import sys
import requests
import multiprocessing
from flask import Flask, request


class AbstractServer:
    port = 9090
    name = ""

    def __init__(self):
        pass

    def get_info(self):
        return self.name, self.port

    def health_check(self):
        pass

    def is_indexed(self):
        pass

    def index(self):
        pass

    def query(self):
        pass

    def success_response(self):
        return '{ "success": true }', 200

    def blank_query_response(self):
        return '{ "success": true, "results": [] }', 200

    def error_response(self, code, message):
        return message, code


class MasterServer(AbstractServer):

    def __init__(self):
        self.name = "MasterServer"
        AbstractServer.__init__(self)

    def health_check(self):
        results = self.execute(do_health_check)
        for r in results:
            if r.status_code != 200:
                return self.error_response(502, "All nodes are not up")
        return self.success_response()

    def is_indexed(self):
        results = self.execute(do_is_indexed)
        for r in results:
            if not (r.status_code == 200 and "success" in r.text):
                return self.error_response(502, "Nodes are not indexed")
        return self.success_response()

    def index(self):
        path = request.args.get("path", "")
        results = self.execute(do_index, path)
        return self.success_response()

    def query(self):
        q = request.args.get("q", "")
        results = self.execute(do_query, q)
        r = results[0]
        return r.text, r.status_code

    def execute(self, func, args=None):
        tasks = [(func, (self.port + i + 1, args)) for i in range(3)]
        pool = multiprocessing.Pool(3)
        return pool.map(async_run_star, tasks)


def async_run_star(args):
    return async_run(*args)


def async_run(func, args):
    return func(*args)


def do_health_check(port, ignore):
    return requests.get("http://127.0.0.1:%d/healthcheck" % port)


def do_is_indexed(port, ignore):
    return requests.get("http://127.0.0.1:%d/isIndexed" % port)


def do_index(port, path):
    return requests.get("http://127.0.0.1:%d/index" % port, params={
        "path": path
    })


def do_query(port, q):
    return requests.get("http://127.0.0.1:%d/" % port, params={
        "q": q
    })


class SearchServer(AbstractServer):
    indexed = False

    def __init__(self, pid):
        self.name = "SearchServer-%d" % pid
        self.port += int(pid)
        AbstractServer.__init__(self)

    def health_check(self):
        return self.success_response()

    def is_indexed(self):
        if self.indexed:
            return self.success_response()
        else:
            return self.error_response(200, "Not indexed")

    def index(self):
        self.indexed = True
        return self.success_response()

    def query(self):
        return self.blank_query_response()


def get_cmd_line():
    l = len(sys.argv)

    if l == 1:
        return None
    elif l == 2:
        return sys.argv[1], None
    else:
        return sys.argv[1], sys.argv[2]

app = Flask("")
server = None


def main():
    global server

    cmd, pid = get_cmd_line()
    if cmd is None:
        return 1

    if cmd == "--master":
        server = MasterServer()
    else:
        server = SearchServer(int(pid))

    name, port = server.get_info()
    app.name = name
    app.run(port=port)


@app.route("/healthcheck")
def health_check():
    return server.health_check()


@app.route("/isIndexed")
def is_indexed():
    return server.is_indexed()


@app.route("/index")
def index():
    return server.index()


@app.route("/")
def query():
    return server.query()


if __name__ == "__main__":
    sys.exit(main())
