from fetch_content import *
from utils.db_query import encode_if_necessary
from constants import DATABASE_NAME
import utils.db_access as db_acc


pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


def get_only_db_pages(user_db_port=None, user=None, password=None):
    """
    Get list of pages that were not loaded from API but exist in database.

    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: dataframe
    """

    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            SQL_Query = pd.read_sql_query(
                "SELECT page_id, dbname FROM Scripts WHERE in_api = 0 AND in_database = 1",
                conn,
            )
            df = pd.DataFrame(SQL_Query).applymap(encode_if_necessary)
            df["wiki"] = df["dbname"].map(get_db_map(dbs=list(df["dbname"].values))[0])
        conn.close()
        return df
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Additional script for checking, which pages were fetched only from database."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    local_data = parser.add_argument_group(
        title="Info for connecting to Toolforge from local pc"
    )
    local_data.add_argument(
        "--user-db-port",
        "-udb",
        type=int,
        default=None,
        help="Port for connecting to tables, created by user in Toolforge, "
        "through ssh tunneling, if used.",
    )
    local_data.add_argument(
        "--user", "-u", type=str, default=None, help="Toolforge username of the tool."
    )
    local_data.add_argument(
        "--password",
        "-p",
        type=str,
        default=None,
        help="Toolforge password of the tool.",
    )
    args = parser.parse_args()

    df = get_only_db_pages(args.user_db_port, args.user, args.password)
    get_pages(df, 0, 1, args.user_db_port, args.user, args.password)

    print("Done loading pages only in database.")
