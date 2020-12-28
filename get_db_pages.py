## imports
from fetch_content import *;
from db_script import encode_if_necessary;

pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


def get_only_db_pages():
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            SQL_Query = pd.read_sql_query("select page_id, dbname from Scripts where in_api = 0 and in_database = 1", conn)
            df = pd.DataFrame(SQL_Query).applymap(encode_if_necessary)
            df['wiki'] = df['dbname'].map(get_db_map(dbs=list(df['dbname'].values))[0])
        conn.close()
        return df
    except pymysql.err.OperationalError:
        print('Failure: please use only in Toolforge environment')
        exit(1)

def remove_missed_contents():
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("delete from Scripts where is_missed=1")
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)
    
    print('Removed redundant rows...')

if __name__ == "__main__":
    df = get_only_db_pages()
    get_pages(df, in_api=0, in_database=1)
    # remove_missed_contents()
    print('Done loading pages only in database.')
