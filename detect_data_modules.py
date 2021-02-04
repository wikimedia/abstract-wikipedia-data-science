import argparse

from utils.db_query import query_data_generator, save_data, get_dbs


def detect_data_modules(full_run=False, user_db_port=None, user=None, password=None):
    query = (
        "SELECT page_id, sourcecode"
        "FROM Scripts "
    )
    new_values_query = "WHERE is_data IS NULL"
    save_query = "UPDATE Scripts SET is_data=%s WHERE dbname=%s AND page_id=%s "

    cols = ["page_id", "dbname", "sourcecode", "is_data"]
    function_name = "detect_data_modules"

    if full_run:
        for df in query_data_generator(
            query,
            function_name,
            cols,
            replicas=False,
            user_db_port=user_db_port,
            user=user,
            password=password
        ):
            print("tick")
            #save_data(df, db, function_name, user_db_port, user, password)
    else:
        for df in query_data_generator(
            query + new_values_query,
            function_name,
            cols,
            replicas=False,
            user_db_port=user_db_port,
            user=user,
            password=password
        ):
            print("tock")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Marks modules as data modules based on their sourcecode."
        "By default is run only on Scripts, where is_data field in DB is not set."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--full-run",
        "-f",
        action="store_true",
        help="Set to check all the entries in the database.",
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
        "--user",
        "-u",
        type=str,
        default=None,
        help="Toolforge username of the tool."
    )
    local_data.add_argument(
        "--password",
        "-p",
        type=str,
        default=None,
        help="Toolforge password of the tool.",
    )
    args = parser.parse_args()

    detect_data_modules(args.full_run, args.user_db_port, args.user, args.password)