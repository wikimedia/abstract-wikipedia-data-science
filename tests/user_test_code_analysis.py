import argparse
import pandas as pd

import utils.db_access as db_acc
import utils.db_query
from constants import DATABASE_NAME, ANALYSIS_BATCH_SIZE, ANALYSIS_TEST_OUT_FILE

import code_analysis


def print_clustering_to_md(df, full_output=False):
    df = df.sort_values(by=['group'])

    with open(ANALYSIS_TEST_OUT_FILE, 'w') as f:
        if not full_output:
            # For non-unique entries
            print("_Printing only groups with multiple items_\n", file=f)
            df = df[df.duplicated(subset=['group'], keep=False)]
        else:
            # For all entries
            print("_Printing all groups with items_\n", file=f)

        for elem in df.group.tolist():
            print("## Group " + str(elem) + "\n", file=f)
            curr_group_df = df.where(df['group'] == elem)
            for i, curr_elem in enumerate(curr_group_df.group.tolist()):
                print("#### Title: '" + curr_group_df.iloc[i]['title'] + "'\n", file=f)
                print("```lua\n" + curr_group_df.iloc[i]['sourcecode'] + "\n```\n", file=f)

    print("Printing test results finished")


def test_levenshtein_clusterization(full_output=False, user_db_port=None, user=None, password=None):
    """
    Current way of clusterization sometimes might need some "fine tuning",
    so this function is created to test levenshtein_clusterization() on smaller sizes of input
    with results, accessible through text files.
    """
    try:
        conn = db_acc.connect_to_user_database(
            DATABASE_NAME, user_db_port, user, password
        )
        query = """
        select dbname, title, sourcecode, length
        from Scripts
        order by rand()
        limit 
        """

        with conn.cursor() as cur:
            cur.execute(query + str(ANALYSIS_BATCH_SIZE))
            df = pd.DataFrame(cur, columns=['dbname', 'title', 'sourcecode', 'length'])

            res = code_analysis.levenshtein_clasterization(df)
            print_clustering_to_md(res, full_output)
        utils.db_query.close_conn(conn)
    except Exception as err:
        print("Something went wrong.\n", err)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Provides tests, that should be run by user for code analysis part."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--full-output",
        "-f",
        action="store_true",
        help="Output file will have all clustering results."
             "If not set, only groups with more then one entry will be printed."
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

    test_levenshtein_clasterization(args.full_output, args.user_db_port, args.user, args.password)

