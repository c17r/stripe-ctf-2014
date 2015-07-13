#!/usr/bin/env python
import os
import sys
import multiprocessing
import traceback
import logging
import MySocket
import MyHTTPServer
import Sql
import Raft

logging.basicConfig(level=logging.DEBUG)


class Server:
    path = None
    sql_path = None
    address = None
    http_server = None
    sql_server = None
    raft_server = None
    sql_count = -1
    lock = None

    def __init__(self, path, address):
        self.path = path
        self.address = address
        self.sql_path = os.path.join(path, "storage.sql")
        self.sql_server = Sql.Sql(self.sql_path)
        self.lock = multiprocessing.RLock()

    def _handle_sql(self, request):
        sql = request["post_data"]

        if self.raft_server.state != Raft.Raft.STATE_LEADER:
            try:
                primary_o = self._primary_proxy(sql)
            except Exception as e:
                logging.exception("_handle_sql")
                return "_handle_sql: %s" % e.message, 400

            return primary_o, 200

        job = {
            "sql_count": self.sql_count + 1,
            "sql": sql
        }

        try:
            err2 = None
            o = None
            job_id = self.raft_server.add_job(job)
            if job_id is not False:
                o, err2 = self.sql_server.execute(job["sql"])
                self.lock.acquire()
                self.sql_count = job["sql_count"]
                o = "SequenceNumber: %d\n%s" % (self.sql_count, o)
                self.lock.release()
                self.raft_server.confirm_job(job_id)
        except Exception as e:
            logging.exception("_handle_sql")
            return "_handle_sql: %s" % e.message, 400

        if err2:
            return "Error" + err2, 500
        else:
            return o, 200

    def _primary_proxy(self, data):
        primary = MyHTTPServer.HTTPClient(MySocket.UnixClient)
        primary_address = self.raft_server.leader
        if not primary_address:
            logging.debug("***THIS SHOULDN'T HAPPEN***")
            logging.debug("peers = %s" % self.raft_server.peers)
            logging.debug("leader = %s" % self.raft_server.leader)
            logging.debug("myself = %s" % self.raft_server.myself)
            logging.debug("term = %d" % self.raft_server.term)
            logging.debug("state = %d" % self.raft_server.state)
        return primary.execute(primary_address, "POST", "/sql", data)

    def _handle_raft(self, request):
        return self.raft_server.handle_raft_request(request)

    def _handle_raft_write(self, job):
        o, err3 = self.sql_server.execute(job["sql"])
        self.lock.acquire()
        self.sql_count = job["sql_count"]
        o = "SequenceNumber: %d\n%s" % (self.sql_count, o)
        self.lock.release()

    def _ensure_empty_sql(self):
        if os.access(self.sql_path, 0):
            os.remove(self.sql_path)

    def listen_and_serve(self, primary):

        self.raft_server = Raft.Raft(self.address, primary)
        self.raft_server.register_write_handler(self._handle_raft_write)

        self.http_server = MyHTTPServer.HTTPServer(self.address)
        self.http_server.register_handler("sql", self._handle_sql)
        self.http_server.register_handler("r", self._handle_raft)
        self.http_server.start()



def main():
    return 1


if __name__ == "__main__":
    sys.exit(main())