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
    return sql_to_df(db, query)

def get_iwl_info(db):
    ## But `Module:` is not the only prefix for Scribunto modules.
    ## It is different for all languages and there are mix and matches. 
    ## e.g bnwiki has `Modules:` and also `মডিউল:`
    
    ## TODO: Collect list of Modules prefixes/how else to identify modules from iwl table?
    q = (
            "SELECT page_id, page_title, "
            "COUNT(iwl_from) AS iwls "
            "FROM page "
            "INNER JOIN iwlinks "
            "    ON iwl_title LIKE CONCAT('Module:', page_title) "
            "    AND page_namespace=828 "
            "    AND page_content_model='Scribunto' " 
            "GROUP BY page_id, page_title "
            )
    return sql_to_df(db, query)