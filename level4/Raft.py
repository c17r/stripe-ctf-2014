#!/usr/bin/env bash
import os
import sys
import random
import json
import logging
from datetime import datetime
import MyHTTPServer
import MySocket
import threading
import multiprocessing
import base64
import hashlib

logging.basicConfig(level=logging.DEBUG)


class Raft:
    RAFT_URL = "/r"
    STATE_FOLLOWER = 0
    STATE_CANDIDATE = 1
    STATE_LEADER = 2

    leader = None
    myself = None
    peers = None
    term = None
    vote_count = None
    state = None

    jobs = []
    commit_point = 0
    write_func = None

    heartbeat_count = -1
    election_count = -1
    raft_timer = None
    raft_timeout = 100

    def __init__(self, myself, leader=None):
        self.myself = myself
        self.leader = leader
        self.peers = []
        if not self.leader:
            self.peers.append(self.myself)
            self.heartbeat_timeout = 1000
            self.election_timeout = 2000
            self.term = 0
            self._become_leader()
        else:
            self._info_from_leader()
            self.heartbeat_timeout = 1000
            self.election_timeout = 2000
            self._become_follower()

    @staticmethod
    def reset_timer(timer, timeout, func):
        if timer:
            timer.cancel()
        t = threading.Timer(timeout/1000.0, func)
        t.start()
        return t

    @staticmethod
    def cancel_timer(timer):
        if timer:
            timer.cancel()

    @staticmethod
    def create_socket():
        return MyHTTPServer.HTTPClient(MySocket.UnixClient)

    def _log(self, message):
        logging.debug("%s [%s] %s\n" % (datetime.now(),
                                        os.path.basename(self.myself),
                                        message))

    def _reset_heartbeat(self):
        self.heartbeat_count = 0

    def _reset_election(self):
        self.election_count = 0

    def _cancel_heartbeat(self):
        self.heartbeat_count = -1

    def _cancel_election(self):
        self.election_count = -1

    def _pulse

    def _do_heartbeat(self):
        self._send_heartbeat()
        self._reset_heartbeat()

    def _do_election(self):
        self._become_candidate(self.term+1)

        result, term = self._send_election_req()
        term = int(term)
        if result:
            self._become_leader()
        else:
            new_term = term if term > self.term else None
            self._become_follower(new_term)

    def _info_from_leader(self):
        rtn = self._send_info_req()
        if not rtn:
            return
        data = rtn.split("\0")
        self.heartbeat_timeout = int(data[0])
        self.election_timeout = int(data[1])
        self.term = int(data[2])
        self.peers = data[3:]

    def _send_info_req(self):
        data = "0\0%s" % self.myself
        leader = Raft.create_socket()
        return leader.execute(self.leader, "POST", self.RAFT_URL, data)

    def _success_response(self):
        return "1\0%d" % self.term, 200

    def _failure_response(self):
        return "0\0%d" % self.term, 200

    def _all_but_me(self):
        peeps = self.peers[:]
        if self.myself in peeps:
            peeps.remove(self.myself)
        return peeps

    def _send_election_req(self):
        data = "1\0%d\0%s" % (self.term, self.myself)

        for peer in self._all_but_me():
            sock = Raft.create_socket()
            rtn = sock.execute(peer, "POST", self.RAFT_URL, data)
            if not rtn:
                vote, term = False, -1
            else:
                vote, term = rtn.split("\0")
            term = int(term)
            if term > self.term:
                return False, term # term VERY important here

            self.vote_count += int(vote)

        return self.vote_count >= ((len(self.peers) / 2) + 1), -1 # don't care about term here

    def _send_heartbeat(self):
        logging.debug(threading.currentThread())
        data = "3\0%d\0%s\0%d\n" % (self.term, self.myself, self.commit_point)
        data += "\0".join(self.peers) + "\n"
        data += "\n"

        for peer in self._all_but_me():
            sock = Raft.create_socket()
            rtn = sock.execute(peer, "POST", self.RAFT_URL, data)
            if not rtn:
                resp, term = "", -1
            else:
                resp, term = rtn.split("\0")
            term = int(term)
            if term > self.term:
                self._become_follower(term)

    def _send_append_entries(self, commit=None):

        cp = commit if commit else self.commit_point

        log = self.jobs
        #log = cPickle.dumps(log)
        log = json.dumps(log)
        log = base64.b64encode(log)
        md5 = hashlib.md5(log)

        data = "2\0%d\0%s\0%d\n" % (self.term, self.myself, cp)
        data += "\0".join(self.peers) + "\n"
        data += "%s\0%s\0" % (md5, log) + "\n"

        majority = 1

        for peer in self._all_but_me():
            sock = Raft.create_socket()
            rtn = sock.execute(peer, "POST", self.RAFT_URL, data)
            if not rtn:
                resp, term = "", -1
            else:
                resp, term = rtn.split("\0")
            term = int(term)
            if term > self.term:
                self._become_follower(term)
                return False
            if resp:
                majority += int(resp)

        return majority >= ((len(self.peers) / 2) + 1)

    def _become_follower(self, term=None, leader=None):
        if term:
            self.term = term
        if leader is not None and self.leader != leader:
            logging.debug("_become_follower, leader is %s" % leader)
            self.leader = leader

        self.state = Raft.STATE_FOLLOWER
        self._cancel_heartbeat()
        self._reset_election()

    def _become_candidate(self, term=None):
        logging.debug("_become_candidate")
        if term:
            self.term = term
        self.state = Raft.STATE_CANDIDATE
        self.vote_count = 1
        self._cancel_heartbeat()

    def _become_leader(self):
        logging.debug("_become_leader")
        self.state = Raft.STATE_LEADER
        self._cancel_election()
        self._send_heartbeat()
        self._reset_heartbeat()

    def _handle_info_req(self, requester):
        if requester not in self.peers:
            self.peers.append(requester)
        rtn = "%d\0%d\0%d\0%s" % (self.heartbeat_timeout,
                                  self.election_timeout,
                                  self.term,
                                  "\0".join(self.peers)
        ), 200
        return rtn

    def _handle_election(self, data):
        term, _ = data.split("\0")
        term = int(term)

        ret = self._failure_response()
        if term > self.term:
            self._become_follower(term)
            ret = self._success_response()

        return ret

    def _handle_entries(self, data):
        lines = [line.rstrip() for line in data.split("\n")]

        term, leader, commit = lines[0].split("\0")
        commit = int(commit)
        term = int(term)
        self.peers = lines[1].split("\0")

        if term < self.term:
            return self._failure_response()

        if term >= self.term:
            self._become_follower(term, leader)

        h, log, _ = lines[2].split("\0")
        md5 = hashlib.md5(log)

        if h == md5:
            logging.debug("MD5 GOOD")
        else:
            logging.debug("MD5 BAD")

        log = base64.b64decode(log)
        #log = cPickle.loads(log)
        log = json.loads(log)



        self.jobs = log

        if 0 < commit > self.commit_point:
            start = self.commit_point
            for i in xrange(start, commit):
                self.write_func(log[i])
            self.commit_point = commit

        return self._success_response()

    def _handle_heartbeat(self, data):
        lines = data.split("\n")

        term, leader, _ = lines[0].split("\0")
        term = int(term)
        self.peers = lines[1].split("\0")

        if term < self.term:
            return self._failure_response()

        if term >= self.term:
            self._become_follower(term, leader)

        return self._success_response()

    def handle_raft_request(self, req):
        try:
            self._cancel_election()

            raw = req["post_data"]
            pos = raw.find("\0")
            action = int(raw[:pos])
            data = raw[pos+1:]

            if action == 0:
                rtn = self._handle_info_req(data)

            if action == 1:
                rtn = self._handle_election(data)

            if action == 2:
                rtn = self._handle_entries(data)

            if action == 3:
                rtn = self._handle_heartbeat(data)

            return rtn

        except Exception as e:
            logging.exception("handle_raft_request")
            return "handle_raft_request: %s" % e.message, 400
        finally:
            if self.state == Raft.STATE_FOLLOWER:
                self._reset_election()

    def register_write_handler(self, func):
        self.write_func = func

    def add_job(self, new_item):
        self.jobs.append(new_item)
        job_id = len(self.jobs)

        rtn = self._send_append_entries(-1)
        if rtn is False:
            return False
        return job_id

    def confirm_job(self, job_id):
        self.commit_point = job_id
        self._send_append_entries()


def main():
    return 1


if __name__ == "__main__":
    sys.exit(main())