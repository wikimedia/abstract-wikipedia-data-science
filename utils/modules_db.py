import toolforge
import pandas as pd

DATABASE_NAME = 's54588__data'

def populate_table():
    query = "SELECT DISTINCT LEFT(title, LOCATE(':',title)-1) AS module FROM Scripts;"
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute(query)
            for module in modules:
                print(module)
                break
                cur.execute("INSERT INTO Module (module) values %s", moduele[0])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)

if __name__ == "__main__":
    """
    The `Module` table contains list of all prefix to Scribunto modules like Module, মডিউল, ماجول etc.
    """
    populate_table()