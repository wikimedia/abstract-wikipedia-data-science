import pandas as pd
import numpy as np
import csv
import sys

import toolforge
import pymysql

DATABASE_NAME = 's54588__data'


def compare_with_saved_by_db():
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("select count(*) from Scripts where in_api = 1 and in_database = 0")
            print("DB info: Entries captured from api, but not from database: ", cur.fetchone()[0])

            cur.execute("select count(*) from Scripts where in_api = 0 and in_database = 1")
            print("DB info: Entries captured from database, but not from api: ", cur.fetchone()[0])
        conn.close()
    except pymysql.err.OperationalError:
        print('Failure: please use only in Toolforge environment')
        exit(1)


compare_with_saved_by_db()
