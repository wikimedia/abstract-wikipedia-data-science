import toolforge
import pandas as pd
import pymysql

from db_script import encode_if_necessary;

def sql_to_df(db, query):
    conn = connectdb(db)
    with conn.cursor() as cur:
        cur.execute("use "+db+'_p')
        SQL_Query = pd.read_sql_query(query, conn)
        df = pd.DataFrame(SQL_Query).applymap(encode_if_necessary)
    conn.close()
    return df

def get_rev_info(db):
    query = (
                "SELECT page.page_id, "
                "COUNT(rev.rev_page) as edits, SUM(rev.rev_minor_edit) AS minor_edits, "
                "MIN(rev.rev_timestamp) as first_edit, MAX(rev.rev_timestamp) AS last_edit, "
                "SUM(case when act.actor_user is null then 1 else 0 end) AS anonymous_edits "
                "FROM page "
                "INNER JOIN revision AS rev "
                "    ON page.page_id=rev.rev_page "
                "    AND page.page_namespace=828 "
                "    AND page.page_content_model='Scribunto' "
                "LEFT JOIN actor AS act "
                "    ON rev.rev_actor=act.actor_id "
                "GROUP BY page.page_id"
            )
    return sql_to_df(db, query)

def get_iwl_info(db):
    query = (
                "SELECT page.page_id, "
                "COUNT(iwl.iwl_from) as iwls "
                "FROM page "
                "INNER JOIN iwlinks AS iwl "
                "    ON page.page_id=iwl.iwl_from "
                "    AND page.page_namespace=828 "
                "    AND page.page_content_model='Scribunto' "
                "GROUP BY page.page_id"
            )
    return sql_to_df(db, query)