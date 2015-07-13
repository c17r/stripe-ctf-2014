#!/usr/bin/env python
import os
import sys
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)


class Sql():
    path = ""

    def __init__(self, path):
        self.path = path

    def execute(self, sql):
        output = ""
        error = ""
        logging.debug("Execute SQL")

        for s in sql.split(";"):
            o, err1 = self._inner_execute(s)
            if len(o) > 0:
                output += o
            if len(err1) > 0:
                error += err1
                break

        return output, error

    def _inner_execute(self, sql):
        conn = sqlite3.connect(os.path.basename(self.path))
        output = ""
        error = ""

        try:
            for row in conn.execute(sql):
                t = [str(i) for i in row]
                output += "|".join(t) + "\n"

            conn.commit()
        except sqlite3.Error as e:
            logging.exception("_inner_execute")
            error = e.args[0]
            conn.rollback()
        finally:
            conn.close()

        return output, error


def main():
    return 1

if __name__ == "__main__":
    sys.exit(main())