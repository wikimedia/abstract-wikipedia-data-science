import argparse

from utils.db_query import query_data_generator, save_data
from utils.sourcecode_processing import remove_comments, check_if_data_function


def detect_data_modules(full_run=False, user_db_port=None, user=None, password=None):
    """
    Gets sourcecodes of Lua functions from user's database and evaluates
    whether function is considered to be 'data function'
    (used only for storing information), saving it's results back to user's database.

    :param full_run: determines whether to check all scripts or only unhandled ones.
    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """
    query = (
        "SELECT page_id, dbname, sourcecode, is_data "
        "FROM Scripts "
    )
    new_values_query = "WHERE is_data IS NULL"

    cols = ["page_id", "dbname", "sourcecode", "is_data"]
    function_name = "detect_data_modules"

    if not full_run:
        query += new_values_query

    for df in query_data_generator(
            query,
            function_name,
            cols,
            db="user_db",
            replicas=False,
            user_db_port=user_db_port,
            user=user,
            password=password,
            no_offset=True
    ):
        sourcecodes = df.loc[:, 'sourcecode']
        for i in range(sourcecodes.shape[0]):
            curr_code = remove_comments(sourcecodes.iat[i])
            df.loc[i, 'is_data'] = check_if_data_function(curr_code)

        grouped = df.groupby(df["dbname"])
        for db_name in df["dbname"].unique():
            save_data(
                grouped.get_group(db_name),
                db_name,
                function_name,
                user_db_port,
                user,
                password)

    if full_run:
        print("Done evaluating all Lua scripts content.")
    else:
        print("Done evaluating new Lua scripts content.")


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
