import toolforge
import argparse
from constants import DATABASE_NAME
import utils.db_access as db_acc


def remove_missed_contents(user_db_port, user, password):
    """
    Removes pages with missing content or data.

    :param user_db_port: port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: None
    """

    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        with conn.cursor() as cur:
            cur.execute("delete from Scripts where is_missed=1")
            cur.execute("delete from Scripts where in_api=0 or in_database=0")
        conn.commit()
        conn.close()
    except Exception as err:
        print("Something went wrong. Could not delete rows. \n", err)

    print("Removed redundant rows...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Removes all redundant rows from Scripts table."
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

    remove_missed_contents(args.user_db_port, args.user, args.password)