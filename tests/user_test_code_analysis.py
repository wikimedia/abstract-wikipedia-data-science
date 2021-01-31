import argparse

from .. import code_analysis

import utils.db_access as db_acc
from utils.db_query import query_data_generator, save_data, get_dbs
from constants import DATABASE_NAME


def test_levenshtein_clasterization(user_db_port=None, user=None, password=None):
    """
    Current way of clasterization sometimes might need some "fine tuning",
    so this function is created to test levenshtein_clasterization() on smaller sizes of input
    with results, accessible through text files.
    """
    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            cur.execute(
                ""
            )
        conn.close()
    except Exception as err:
        print("Something went wrong.\n", err)
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Provides tests, that should be run by user for code analysis part."
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

    test_levenshtein_clasterization(args.user_db_port, args.user, args.password)

