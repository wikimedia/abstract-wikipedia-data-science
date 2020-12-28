DATABASE_NAME = 's54588__data'

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
    remove_missed_contents()