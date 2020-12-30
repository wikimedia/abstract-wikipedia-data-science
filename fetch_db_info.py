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

def get_revision_info(db, replicas_port=None, user=None, password=None):
    ## Number of revisions and information info about edits of the Scribunto modules
    query = (
                "SELECT page_id, "
                "COUNT(rev_page) AS edits, SUM(rev_minor_edit) AS minor_edits, "
                "MIN(rev_timestamp) AS first_edit, MAX(rev_timestamp) AS last_edit, "
                "SUM(case when actor_user is null then 1 else 0 end) AS anonymous_edits, "
                "COUNT(DISTINCT actor_user) AS editors "
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

def get_iwlinks_info(db, user_db_port=None, replicas_port=None, user=None, password=None):
    ## Number of inter wiki pages that referenced a module
    ## iwls from other dbs need to be added for each module

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

def get_pagelinks_info(db, replicas_port=None, user=None, password=None):
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

def get_langlinks_info(db, replicas_port=None, user=None, password=None):
    ## Number of languages links a module has (ll)
    ## Number of languages a module is available in (ll+1)
    ## Use the lanlink table more to find out language independent subset of modules

    query = (
            "SELECT page_id, COUNT(DISTINCT ll_lang) AS langs "
            "FROM page "
            "INNER JOIN langlinks "
            "    ON ll_from=page_id "
            "    AND page_namespace=828 "
            "    AND page_content_model='Scribunto' "
            "GROUP BY page_id "
    )
    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

def get_templatelinks_info(db, replicas_port=None, user=None, password=None):
    ## Number of transclusions of a module

    query = (
            "SELECT page_id, "
            "COUNT(DISTINCT tl_from) as transcluded_in "
            "FROM page "
            "INNER JOIN templatelinks "
            "    ON page_title=tl_title "
            "    AND page_namespace=828 "
            "    AND page_content_model='Scribunto' "
            "    AND tl_namespace=828 "
            "GROUP BY page_id"
    )
    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

def get_transclusions_info(db, replicas_port=None, user=None, password=None):
    ## Number of modules transcluded in a module
    ## this includes docs and other stuffs too
    ## so we need to filter by namespace and content_model
    ## The query makes sure both from and to pages are Scribunto modules

    query = (
            "SELECT tl_from, COUNT(DISTINCT tl_title) as transclusions "
            "FROM page "
            "INNER JOIN templatelinks "
            "    ON page_id=tl_from "
            "    AND tl_from_namespace=828 "
            "    AND tl_namespace=828 "
            "    AND page_namespace=828 "
            "    AND page_content_model='Scribunto'"
            "WHERE tl_title IN "
            "    ("
            "        SELECT page_title "
            "        FROM page "
            "        WHERE page_namespace=828 AND page_content_model='Scribunto' "
            "    ) "
            "GROUP BY tl_from"
    )

    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

def get_categories_info(db, replicas_port=None, user=None, password=None):
    ## Number of categories a module is included in
    ## There is not concrete list of categores to look for.
    ## We can list it ourselves, but then again it varies according to language.
    ## If required, use the category table to identify important categories

    q = (
        "SELECT page_id, COUNT(DISTINCT cl_to) AS categories "
        "FROM page "
        "INNER JOIN categorylinks "
        "    ON cl_from=page_id "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "GROUP BY page_id "
    )

    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

def get_edit_protection_info(db, replicas_port=None, user=None, password=None):
    ## Protection level for `edit` for the modules

    q = ("SELECT page_id, pr_level AS pr_level_edit FROM page_restrictions "
        "INNER JOIN page "
        "    ON page_id=pr_page "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pr_type='edit'"
    )

    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

def get_move_protection_info(db, replicas_port=None, user=None, password=None):
    ## Protection level for `move` for the modules

    q = ("SELECT page_id, pr_level AS pr_level_move FROM page_restrictions "
        "INNER JOIN page "
        "    ON page_id=pr_page "
        "    AND page_namespace=828 "
        "    AND page_content_model='Scribunto' "
        "    AND pr_type='move'"
    )

    return sql_to_df(db=db, query=query, replicas_port=replicas_port, user=user, password=password)

def get_most_common_tag_info(db, replicas_port=None, user=None, password=None):
    ## Comma separated most common tag names for each page
    ## See the inline view (subquery) for details on each page

    q = (
    "select tagcount.page_id, GROUP_CONCAT(ctd_name) as tags "
    "from "
        "(select page_id, ctd_name, count(*) as tags "
         "from change_tag "
         "inner join change_tag_def "
         "on ct_tag_id=ctd_id "
         "inner join revision "
         "on ct_rev_id=rev_id "
         "inner join page "
         "on rev_page=page_id "
         "and page_namespace=828 "
         "and page_content_model='Scribunto' "
         "group by page_id, ctd_name "
         ") as tagcount "
    "inner join "
         "(select page_id, max(tags) as most_common_tag_count from "
            "(select page_id, ctd_name, count(*) as tags "
            "from change_tag "
            "inner join change_tag_def "
            "on ct_tag_id=ctd_id "
            "inner join revision "
            "on ct_rev_id=rev_id "
            "inner join page "
            "on rev_page=page_id "
            "and page_namespace=828 "
            "and page_content_model='Scribunto' "
            "group by page_id, ctd_name "
            ") as tagcount "
        "group by page_id) as mosttag "
        "on mosttag.page_id=tagcount.page_id "
        "and tagcount.tags=mosttag.most_common_tag_count "
    "group by tagcount.page_id"
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
