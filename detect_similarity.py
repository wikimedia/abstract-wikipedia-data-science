import pandas as pd
import numpy as np
import argparse
from scipy.sparse import vstack
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer

from utils.db_query import *
import utils.db_access as db_acc
from constants import DATABASE_NAME


def get_tfidf(df, maxlen=20000, ngram=(3, 7)):
    vectorizer = TfidfVectorizer(ngram_range=ngram, token_pattern=r"(?u)\w\w+|[^\w\s*]")
    return vectorizer.fit_transform(df["sourcecode"].apply(lambda x: x[:maxlen]).values)


def find_clusters(df, X, eps=0.2, min_samples=2):
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    return df.assign(group=clustering.labels_), clustering


def store_data(df, col):
    pass


def get_similarity(with_data, user_db_port, user, password):
    ## First clear cluster and cluster_wo_data columns
    query = "SELECT page_id, dbname, sourcecode FROM Scripts"
    if not with_data:
        query += " WHERE is_data=0"

    df = pd.DataFrame()
    tfidf_X = None

    for code_df in query_data_generator(
        query,
        "get_similarity",
        ["page_id", "dbname", "sourcecode"],
        DATABASE_NAME,
        None,
        user_db_port,
        user,
        password,
        False,
        500,
    ):
        X = get_tfidf(code_df)
        tfidf_X = vstack((tfidf_X, X))

        del code_df["sourcecode"]
        df = df.append(code_df, ignore_index=True)
        del code_df
        del X

    df, clustering = find_clusters(df, tfidf_X)
    print(
        df.iloc[clustering.core_sample_indices_]
        .groupby("group")
        .agg({"page_id": "count"})
    )

    ## separate what data to store and what to re-cluster (-1 and 1-2 from each cluster)

    col = "cluster" if with_data else "cluster_wo_data"
    store_data(df, col)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detects similar modules and saves group id in Scripts table."
        "To use from local PC, provide all the additional flags needed for "
        "establishing connection through ssh tunneling."
        "More help available at "
        "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument(
        "--with-data",
        "-d",
        action="store_true",
        help="Whether to include modules that are marked as data modules.",
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
    get_similarity(args.with_data, args.user_db_port, args.user, args.password)
