import toolforge
import pandas as pd
import pymysql
import argparse
import mwapi

import utils.db_access as db_acc
from db_script import encode_if_necessary;

DATABASE_NAME = 's54588__data'

def sql_to_df(query, db=None, user_db_port=None, replicas_port=None, user=None, password=None):
    try:
        if replicas_port:
            conn = db_acc.connect_to_replicas_database(db, replicas_port, user, password)
            db = db+'_p'
        else:
            conn = db_acc.connect_to_user_database(DATABASE_NAME, user_db_port, user, password)
            db = DATABASE_NAME

        with conn.cursor() as cur:
            cur.execute("use "+db)
            SQL_Query = pd.read_sql_query(query, conn)
            df = pd.DataFrame(SQL_Query).applymap(encode_if_necessary)
        conn.close()
        return df
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)

def get_rev_info(db, replicas_port=None, user=None, password=None):
    ## Number of revisions and information info about edits of the Scribunto modules
    query = (
                "SELECT page_id, "
                "COUNT(rev_page) AS edits, SUM(rev_minor_edit) AS minor_edits, "
                "MIN(rev_timestamp) AS first_edit, MAX(rev_timestamp) AS last_edit, "
                "SUM(case when actor_user is null then 1 else 0 end) AS anonymous_edits "
                "FROM page "
                "INNER JOIN revision "
                "    ON page_id=rev_page "
                "    AND page_namespace=828 "
                "    AND page_content_model='Scribunto' "
                "LEFT JOIN actor "
                "    ON rev_actor=actor_id "
                "GROUP BY page_id"
            )
    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

def get_iwl_info(db, user_db_port=None, replicas_port=None, user=None, password=None):
    ## Number of inter wiki pages that referenced a module

    """
    `Module:` is not the only prefix for Scribunto modules.
    It is different for languages e.g `মডিউল:`, ماجول ,ماڈیول
    So, url was matched with iwl_title
    """
        
    create_query = (
        "create table Iwlinks ("
        "    iwl_from int unsigned, "
        "    iwl_prefix varchar(32), "
        "    iwl_title text, "
        "    primary key (iwl_from, iwl_prefix, iwl_title)"
        ")"
        )
    insert_query = (
        "insert into Iwlinks(iwl_from, iwl_prefix, iwl_titile) "
        "values(%s, %s, %s) "
        "on duplicate key update iwl_title = %s"
        )
    drop_query = ("drop table Iwlinks")
    query = (
            "SELECT page_id, dbname, COUNT(DISTINCT iwl_from) AS iwls "
            "FROM Scripts "
            "INNER JOIN "
            "    ("
            "        SELECT iwl_from, REPLACE(url, '$1', iwl_title) AS iwl_url "
            "        FROM Interwiki "
            "        INNER JOIN Iwlinks "
            "        ON prefix=iwl_prefix "
            "    ) AS iwl "
            "ON url=iwl_url "
            "GROUP BY (page_id, dbname)"
        )

    conn_db = db_acc.connect_to_user_database(DATABASE_NAME, user_db_port, user, password)
    conn = db_acc.connect_to_replicas_database(db, replicas_port, user, password)
    with conn_db.cursor() as db_cur, conn.cursor() as cur:
        db_cur.execute(create_query)
        cur.execute("use "+db+'_p')
        cur.execute("select * from iwlinks")
        for val in cur:
            db_cur.execute(insert_query, [val[0], val[1], val[2], val[2]])
        df = sql_to_df(query=query, user_db_port=user_db_port, user=user, password=password)          
        db_cur.execute(drop_query)
    conn_db.commit()
    conn_db.close()
    conn.close()
    return df

def get_interwiki(user_db_port=None, user=None, password=None):

    ## Get interwiki mapping from API
    user_agent = toolforge.set_user_agent('abstract-wiki-ds')
    session = mwapi.Session('https://en.wikipedia.org', user_agent=user_agent)
    params = {
        'action':'query',
        'format':'json',
        'meta':'siteinfo',
        'siprop':'interwikimap'
    }
    result = session.get(params)
    ret = result['query']['interwikimap']

    ## Save interwiki mapping to user_db
    query = (
        "insert into Interwiki(prefix, url) values(%s, %s) "
        "on duplicate key update url = %s"
        )
    try:
        conn = db_acc.connect_to_user_database(DATABASE_NAME, user_db_port, user, password)
        with conn.cursor() as cur:
            for mp in ret:
                cur.execute(query, (mp['prefix'], mp['url'], mp['url']))
        conn.commit()
        conn.close()
    except Exception as err:
        print('Something went wrong.\n', err)
        exit(1)

def get_pl_info(db, replicas_port=None, user=None, password=None):
    ## Number of (in-wiki) pages that referenced a module
    query = (
                "SELECT page_id, "
                "COUNT(DISTINCT pl_from) as pls "
                "FROM page "
                "INNER JOIN pagelinks "
                "    ON page_title=pl_title "
                "    AND page_namespace=828 "
                "    AND page_content_model='Scribunto' "
                "    AND pl_namespace=828 "
                "GROUP BY page_id"
            )
    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=""
    )
    parser.add_argument("--interwiki", "-iw", action="store_true",
                        help="Whether interwiki-table content should be re-fetched.")
    parser.add_argument("--local", "-l", action="store_true",
                        help="Connection is initiated from local pc.")
    local_data = parser.add_argument_group(title="Info for connecting to Toolforge from local pc")
    local_data.add_argument("--user-db-port", "-udb", type=int,
                            help="Port for connecting to tables, created by user in Toolforge, "
                                 "through ssh tunneling, if used.")
    local_data.add_argument("--user", "-u", type=str,
                            help="Toolforge username of the tool.")
    local_data.add_argument("--password", "-p", type=str,
                            help="Toolforge password of the tool.")
    args = parser.parse_args()

    if not args.local:
        if args.interwiki:
            get_interwiki()
    else:
        if args.interwiki:
            get_interwiki(args.user_db_port, args.user, args.password)
