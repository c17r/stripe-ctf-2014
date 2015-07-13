import os
import re
import sys
import json
import grequests
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
        results = self.execute("healthcheck")
        for r in results:
            if r.status_code != 200:
                return self.error_response(502, "All nodes are not up")
        return self.success_response()

    def is_indexed(self):
        results = self.execute("isIndexed")
        for r in results:
            if not (r.status_code == 200 and "success" in r.text):
                return self.error_response(502, "Nodes are not indexed")
        return self.success_response()

    def index(self):
        path = request.args.get("path", "")
        _, folders, _ = next(os.walk(path))
        folders = [path + "/" + folder for folder in folders]
        results = self.execute_search(folders)
        return self.success_response()

    def query(self):
        q = request.args.get("q", "")
        results = self.execute("", {"q": q})
        combined = self._process_json(results)
        response = {
            "success": True,
            "results": combined
        }
        return json.dumps(response), 200

    def _process_json(self, requests):
        rtn = []
        for r in requests:
            data = r.json()
            rtn.extend(data["results"])
        return rtn

    def execute(self, url, params=None):
        base = "http://127.0.0.1:%d/%s"
        tasks = [base % (self.port + i + 1, url) for i in range(3)]
        reqs = (grequests.get(task, params=params) for task in tasks)
        resp = grequests.map(reqs)
        return resp

    def execute_search(self, folders):
        base = "http://127.0.0.1:%d/index"
        port = self.port + 1
        reqs = []
        first_guy = folders[0:-2]
        rest = folders[-2:]

        for folder in first_guy:
            reqs.append(grequests.get(base % port, params={"path": folder}))

        for folder in rest:
            port += 1
            reqs.append(grequests.get(base % port, params={"path": folder}))

        resp = grequests.map(reqs)
        return resp


class SearchServer(AbstractServer):
    indexed = False
    the_index = None

    def __init__(self, pid):
        self.name = "SearchServer-%d" % pid
        self.port += int(pid)
        self.the_index = Index()
        AbstractServer.__init__(self)

    def health_check(self):
        return self.success_response()

    def is_indexed(self):
        if self.indexed:
            return self.success_response()
        else:
            return self.error_response(200, "Not indexed")

    def index(self):
        path = request.args.get("path", "")
        self.the_index.index_tree(path)
        self.indexed = True

        return json.dumps(self.the_index.get_size()), 200

    def query(self):
        q = request.args.get("q", "")
        results = self.the_index.query(q)
        response = {
            "success": True,
            "results": results
        }
        return json.dumps(response), 200


class Index():
    word_split = None
    file_list = []
    word_list = {}
    word_bits = ""

    def __init__(self):
        self.word_split = re.compile("\W+").split

    def get_size(self):
        return {
            "file_list": len(self.file_list),
            "word_list": len(self.word_list),
            "word_bits": len(self.word_bits)
        }

    def index_tree(self, root):
        file_num = len(self.file_list)
        to_remove = os.path.dirname(root) + "/"
        for current, _, files in os.walk(root):
            for f in files:
                path = "%s/%s" % (current, f)
                self._index_words(path, file_num)
                self.file_list.append(path.replace(to_remove, ""))
                file_num += 1

        self.word_bits = "," + ",".join(self.word_list.keys()) + ","

    def _index_words(self, filename, file_num):
        current_line = 1
        with open(filename, "rb") as f:
            for line in f:
                words = self.word_split(line)
                for word in words:
                    if len(word) == 0:
                        continue
                    lc = self.word_list.get(word, [])
                    lc.append((file_num, current_line))
                    self.word_list[word] = lc
                current_line += 1

    def query(self, q):
        results = []
        check = {}
        words = re.findall(r",([^,]*?%s[^,]*?)," % q, self.word_bits)
        for word in words:
            files = self.word_list.get(word, [])
            for file_num, line_num in files:
                entry = "%s:%d" % (self.file_list[file_num], line_num)
                if not check.has_key(entry):
                    results.append(entry)
                    check[entry] = 1

        return sorted(results)


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
