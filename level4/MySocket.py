#!/usr/bin/env python
import os
import sys
import socket
import traceback
import logging
import SocketServer

logging.basicConfig(level=logging.DEBUG)


class CallBack(SocketServer.BaseRequestHandler):
    BUFFER_SIZE = 4096
    cb = None

    def call_back(self, data):
        pass

    def _get_all_data(self):
        data = ''
        while True:
            buf = self.request.recv(self.BUFFER_SIZE)
            data += buf
            if len(buf) == 0:
                break
        return data

    def handle(self):
        req = self._get_all_data()
        resp = self.call_back(req)
        resp = "" if not resp or len(resp) == 0 else resp
        self.request.sendall(resp)


class BaseServer():
    server = None
    handler = None

    def __init__(self, handler):
        self.handler = handler

    def start(self):
        self._create_server()
        self._print_info()
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            pass
        except Exception as e9:
            logging.exception("BaseServer.start")
        finally:
            self.server.shutdown()

    def _create_server(self):
        pass

    def _print_info(self):
        pass


class UnixServer(BaseServer):
    sock_file = None

    def __init__(self, sock_file, handler):
        self.sock_file = sock_file
        BaseServer.__init__(self, handler)

    def _create_server(self):
        #if os.access(self.sock_file, 0):
        #    os.remove(self.sock_file)
        self.server = SocketServer.UnixStreamServer(
            self.sock_file,
            self.handler)
        self.server.allow_reuse_address = True

    def _print_info(self):
        print "starting Unix Socket server on %s" % self.sock_file


class TCPServer(BaseServer):
    address = None
    port = None

    def __init__(self, address, port, handler):
        self.address = address
        self.port = port
        BaseServer.__init__(self, handler)

    def _create_server(self):
        self.server = SocketServer.TCPServer(
            (self.address, self.port),
            self.handler)
        self.server.allow_reuse_address = True

    def _print_info(self):
        print "starting TCP server on %s:%d" % (self.address, self.port)


class BaseClient():
    BUF_SIZE = 4096
    base_sock = None

    def __init__(self):
        pass

    def write(self, message):
        try:
            message = "" if message is None else message
            self._create_sock()
            self.base_sock.sendall(message)
            self.base_sock.shutdown(1)
            response = ""
            while True:
                buf = self.base_sock.recv(self.BUF_SIZE)
                response += buf
                if len(buf) < self.BUF_SIZE:
                    break
        except Exception as e99:
            logging.exception("BaseClient.write")
            traceback.print_stack()
            return None
        finally:
            if self.base_sock:
                self.base_sock.close()

        return response

    def _create_sock(self):
        pass


class UnixClient(BaseClient):
    socket_file = None

    def __init__(self, socket_file):
        self.socket_file = socket_file
        BaseClient.__init__(self)

    def _create_sock(self):
        self.base_sock = socket.socket(family=socket.AF_UNIX)
        self.base_sock.connect(self.socket_file)


class TCPClient(BaseClient):
    address = None
    port = None

    def __init__(self, address, port):
        self.address = address
        self.port = port
        BaseClient.__init__(self)

    def _create_sock(self):
        self.base_sock = socket.socket()
        self.base_sock.connect((self.address, self.port))


def main():
    return 1

if __name__ == "__main__":
    sys.exit(main())