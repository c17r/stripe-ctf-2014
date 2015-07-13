#!/usr/bin/env python
import os
import sys
import copy
import traceback
import logging
from email.utils import formatdate
import SocketServer

logging.basicConfig(level=logging.DEBUG)


class HTTPHandler(SocketServer.BaseRequestHandler):
    BUFFER_SIZE = 4096

    def get_split_url_params(self, params):
        rtn = {}
        for kv in params.split("&"):
            k,v = kv.split("=")
            rtn[k] = v

        return rtn

    def _get_header_field_data(self, line):
        return "".join(line.split(': ')[1:])

    def _process_request_data(self, data):
        verb = ''
        full_url = ''
        url = ''
        params = {}
        user_agent = ''
        host = ''
        length = 0
        post = ''

        lines = data.split('\n')
        data_start = 0

        for i in xrange(len(lines)):
            line = lines[i].rstrip()

            if i == 0:
                verb, full_url, _ = line.split(' ')
                verb = verb.upper()
                continue

            if line.lower().startswith("user-agent:"):
                user_agent = self._get_header_field_data(line)
                continue

            if line.lower().startswith("host:"):
                host = self._get_header_field_data(line)
                continue

            if line.lower().startswith("content-length:"):
                tmp = self._get_header_field_data(line)
                if len(tmp) > 0:
                    length = int(tmp)
                continue

            if len(line) == 0:
                data_start = i + 1
                break

        if verb == "POST" and length > 0:
            post = "\n".join(lines[data_start:])

        if "?" in full_url:
            url = full_url.split("?")[0]
            params = self.get_split_url_params(full_url.split("?")[1:])
        else:
            url = full_url

        return {
            "verb": verb,
            "url": url,
            "get": params,
            "full_url": full_url,
            "user_agent": user_agent,
            "host": host,
            "length": length,
            "post_data": post
        }

    def _get_request_data(self):
        try:
            data = ''
            while True:
                buf = self.request.recv(self.BUFFER_SIZE)
                data += buf
                if len(buf) == 0:
                    break
            return data
        except Exception as e3:
            logging.exception("HTTPHandler._get_request_data")

    def _send_data(self, data):
        data = "" if not data else data
        try:
            self.request.sendall(data)
        except Exception as e4:
            logging.exception("HTTPHandler._send_data")

    def _convert_code(self, code):
        code = int(code)

        if code == 200:
            return "OK"

        if code == 400:
            return "Bad Request"

        if code == 404:
            return "Not Found"

        if code == 500:
            return "Internal Server Error"

        return "Unknown"

    def handle(self):
        try:
            data = self._get_request_data()
            request = self._process_request_data(data)
            handler = self.server.user_handlers.get(request["url"].strip("/"), None)

            if handler:
                h_r = copy.deepcopy(request)
                body, code = handler(h_r)
            else:
                body, code = "File Not Found", 404

            body = "" if not body else body

            http = []
            http.append("HTTP/1.1 %d %s" % (code, self._convert_code(code)))
            http.append("Date: %s" % formatdate(timeval=None, localtime=False, usegmt=True))
            http.append("Content-Length: %d" % len(body))
            http.append("Content-type: text/plain; charset=utf-8")
            http.append("")
            http.append(body)

            self._send_data("\n".join(http))
        except Exception as e5:
            logging.exception("HTTPHandler.handle")
            self._send_data("HTTP/1.1 400 Bad Request")


class HTTPTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    user_handlers = {}
    address = None
    port = None

    def __init__(self, server_address):
        self.address, self.port = server_address.split(":")
        self.port = int(self.port)
        SocketServer.TCPServer.__init__(self, (self.address, self.port), HTTPHandler)
        self.allow_reuse_address = True

    def start(self):
        try:
            print "starting TCP server on %s:%d" % (self.address, self.port)
            self.serve_forever()
        except Exception as e6:
            logging.exception("HTTPTCPServer.start")
        finally:
            self.shutdown()


class HTTPUnixServer(SocketServer.UnixStreamServer):
    user_handles = {}
    sock_file = None

    def __init__(self, server_address):
        self.sock_file = server_address
        #if os.access(self.sock_file, 0):
        #    os.remove(self.sock_file)
        SocketServer.UnixStreamServer.__init__(self, server_address, HTTPHandler)
        self.allow_reuse_address = True

    def start(self):
        try:
            print "starting Unix Socket server on %s" % self.sock_file
            self.serve_forever()
        except Exception as e7:
            logging.exception("HTTPUnixServer.start")
        finally:
            self.shutdown()


class HTTPServer():
    user_handlers = {}
    server_address = None
    server = None

    def __init__(self, server_address):
        self.server_address = server_address

    def _is_unix_server(self):
        rtn = False
        if self.server_address.startswith("."):
            rtn = True
        if self.server_address.startswith("/"):
            rtn = True

        return rtn

    def register_handler(self, url, handler):
        user = self.user_handlers.get(url, None)
        if user:
            return False
        self.user_handlers[url] = handler

    def start(self):
        if self._is_unix_server():
            self.server = HTTPUnixServer(self.server_address)
        else:
            self.server = HTTPTCPServer(self.server_address)

        self.server.user_handlers = self.user_handlers
        self.server.start()


class HTTPClient():
    client = None

    def __init__(self, client):
        self.client = client

    def execute(self, address, verb="GET", url="/", data=None):
        socket = self.client(address)

        request = "%s %s HTTP/1.1\n" % (verb, url)
        request += "Content-Length: %d\n" % len(data)
        request += "\n"
        request += data

        try:
            response = socket.write(request)
        except Exception as e8:
            logging.exception("HTTPClient.execute")
        if not response:
            return response

        lines = [line.rstrip() for line in response.split("\n")]
        data_start = 0
        for i in xrange(len(lines)):
            if len(lines[i]) == 0:
                data_start = i + 1
                break

        return "\n".join(lines[data_start:])


def main():
    return 1

if __name__ == "__main__":
    sys.exit(main())