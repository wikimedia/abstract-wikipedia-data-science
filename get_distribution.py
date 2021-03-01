import pandas as pd
import numpy as np
import argparse
import sys
import copy
from utils.db_query import encode_if_necessary, close_conn
from constants import DATABASE_NAME
import utils.db_access as db_acc


def get_data(feature_names, user_db_port, user, password):
    """
    Collects data from Scripts table, columns include column names in feature names
    and additionally 'edits per editor' and 'edits per day' are calculated.
    Adds 'is_data' column for usage specific to webservice.

    :param feature_names: List of features whose scores are to be calculated
    :param user_db_port: Port for connecting to local Sources table through ssh tunneling, if used.
    :param user: Toolforge username of the tool.
    :param password: Toolforge password of the tool.
    :return: DataFrame
    """
    cols = copy.deepcopy(feature_names)

    if "edits" not in cols:
        cols += ["edits"]
    if "editors" not in cols:
        cols += ["editors"]
    if "major_edits" in cols:
        cols.remove("major_edits")
        cols += ["minor_edits"]

    cols += ["page_id", "dbname", "is_data", "first_edit", "last_edit"]

    query = "SELECT " + ",".join(cols) + " FROM Scripts"

    conn = db_acc.connect_to_user_database(
        DATABASE_NAME, user_db_port, user, password)
    with conn.cursor() as cur:
        cur.execute(query)
        df = pd.DataFrame(
            cur.fetchall(),
            columns=cols,
        ).applymap(encode_if_necessary)
    close_conn(conn)

    df["edits_per_editor"] = (df["edits"] / df["editors"]).replace(np.inf, 0)
    time_range = (df["last_edit"] - df["first_edit"]).apply(
        lambda x: x.days + x.seconds / (24 * 60 * 60)
    )
    df["edits_per_day"] = (df["edits"] / time_range).replace(np.inf, 0)

    if "major_edits" in feature_names:
        df["major_edits"] = df["edits"] - df["minor_edits"]

    return df[
        ["page_id", "dbname", "is_data", "edits_per_editor",
            "edits_per_day"] + feature_names
    ]


def normalize(df):
    """
    Normalizes columns per wiki for a selected number of features (listed in 'cols' variable).

    :param df: DataFrame whose columns are to be normalized
    :return: DataFrame
    """
    cols = [
        "editors",
        "major_edits",
        "anonymous_edits",
        "pls",
        "transcluded_in",
    ]

    for col in cols:
        if col in df.columns:
            df[col + "_norm"] = (
                df[col] / df.groupby("dbname")[col].transform("sum")
            ) * 100
            del df[col]

    return df


def which_percentile(value, d):
    """
    Returns the percentile of 'value' in 'd's distribution.

    :param value: The value whose percentile is required
    :param d: A pandas.Series or Numpy array which represents the distribution
    :return: int
    """
    if len(d) == 0:
        return 0
    return sum(d < value) / len(d)


def get_multipliers(df, threshold=0.87):
    """
    Alters distribution of each column in df such that the heuristic values in
    'limits_num' dictionary is the 'threshold' percentile or less. This ensures
    higher values of certain features get more priority, and the 99.9% of values
    (which are very low) are not prioritized too much. This does NOT change original
    values but simply removes lower values when calculating percentiles.

    :param df: Dataframe of features whose multipliers are to be calculated
    :param threshold: The percentile below which the limits should be in the modified distribution
    :return: dictionary of heuristic limits, dictionary of multipliers
    """

    # List of determined heuristics
    # So far for options between norm and actual numbers, norms are used
    limits_num = {
        "edits_per_editor": 200,
        "edits_per_day": 6000,
        "editors": 20,
        "editors_norm": 5,
        "edits": 300,
        "major_edits": 300,
        "major_edits_norm": 15,
        "anonymous_edits_norm": 10,
        "length": 400000,
        "pls": 1500,
        "pls_norm": 20,
        "categories": 5,
        "langs": 100,
        "transcluded_in": 1e6,
        "transcluded_in_norm": 15,
        "transclusions": 30,
    }

    limits_perc = {}

    for k, v in limits_num.items():

        if k not in df.columns:
            continue

        req_val = 0

        for x in np.arange(1, 0, -0.01):
            val = which_percentile(v, df[df[k] >= x * v][k])
            # The values should be the maximum number below the thereshold
            if val > threshold:
                break
            req_val = x

        limits_perc[k] = req_val

    return limits_num, limits_perc


def get_distribution(df, limits_num, limits_perc):
    """
    Returns modified dataframe by replacing features with respective scores.
    Here scores means 'what percentile is this value in the modified distribution?'.

    :param df: The dataframe containing all the features
    :param limits_num: Dictionary of heuristic limits
    :param limits_perc: Dictionary of multipliers to alter distribution
    :return: DataFrame
    """
    for k in df.columns:
        if k == "page_id" or k == "dbname" or k == "is_data":
            continue
        v = limits_num[k]
        p = limits_perc[k]
        d = df[df[k] >= p * v][k]
        df[k + "_score"] = df[k].apply(lambda x: which_percentile(x, d))
        del df[k]
    return df


def get_score(
    feature_names=[
        "edits_per_editor_score",
        "edits_per_day_score",
        "length_score",
        "langs_score",
        "editors_norm_score",
        "major_edits_norm_score",
        "pls_norm_score",
        "transcluded_in_norm_score",
    ],
    weights=[1, 1, 0.1, 5, 2, 5, 2, 8],
):
    """
    Returns dataframe with scores of each module in the 'score' column.

    :param feature_names: Features against whom final score is to be calculated
    :param weights: The linear weights to give to each feature
    :return: DataFrame
    """

    if (len(feature_names)) != len(weights):
        sys.exit("Number of features is not equal to the number of weights!")
    df = pd.read_csv("data_distribution.csv")
    weights = [w / sum(weights) for w in weights]  # Normalize weights
    df["score"] = df[feature_names].dot(weights)
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate scores for each feature and save scores as csv file."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--feature-names",
        "-fn",
        type=str,
        nargs="+",
        help="Name of the features(columns in Scripts table) to get distribution of."
        "Possible values are editors, edits, major_edits, anonymous_edits, pls, categories, langs,"
        "transcluded_in, transclusions, length, pageviews.",
        default=["editors", "major_edits", "length",
                 "pls", "langs", "transcluded_in"],
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

    df = get_data(args.feature_names, args.user_db_port,
                  args.user, args.password)
    df = normalize(df)
    limits_num, limits_perc = get_multipliers(df)
    df = get_distribution(df, limits_num, limits_perc)
    df.to_csv("data_distribution.csv", index=False)

    # Only to be called from other functions
    # get_score()
