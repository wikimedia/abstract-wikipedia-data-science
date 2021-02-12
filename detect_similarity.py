import pandas as pd
import numpy as np
import re
import argparse
import random
from scipy.sparse import vstack
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.models.fasttext import FastText, load_facebook_vectors, save_facebook_model
from utils.db_query import *
import utils.db_access as db_acc
from constants import DATABASE_NAME


def get_data(
    with_data,
    user_db_port,
    user,
    password,
    maxlen=20000,
):
    ## First clear cluster and cluster_wo_data columns

    query = "SELECT page_id, dbname, LEFT(sourcecode, %s) FROM Scripts" % maxlen
    if not with_data:
        query += " WHERE is_data=0"

    cols = ["page_id", "dbname", "sourcecode"]
    conn = db_acc.connect_to_user_database(DATABASE_NAME, user_db_port, user, password)
    with conn.cursor() as cur:
        cur.execute(query)
        df = pd.DataFrame(cur.fetchall(), columns=cols).applymap(encode_if_necessary)
    close_conn(conn)

    return df


def get_tfidf(df, ngram=(3, 7)):
    vectorizer = TfidfVectorizer(ngram_range=ngram, token_pattern=r"(?u)\w\w+|[^\w\s*]")
    return vectorizer.fit_transform(df["sourcecode"])


def preprocess_text(document):
    pat = r"(?u)\w\w+|[^\w\s]+"
    return re.findall(pat, document)


def train_embedding(
    with_data,
    user_db_port,
    user,
    password,
    limit=10000,
    maxlen=20000,
    embedding_size=32,
):

    ft_model = FastText(
        size=embedding_size,
        window=5,
        min_count=5,
        max_vocab_size=60000,
        sg=1,
    )

    query = "SELECT page_id, dbname, LEFT(sourcecode, %s) FROM Scripts" % maxlen
    if not with_data:
        query += " WHERE is_data=0"

    cols = ["page_id", "dbname", "sourcecode"]
    first_iter = True
    for df in query_data_generator(
        query,
        "detect_similarity",
        cols,
        DATABASE_NAME,
        None,
        user_db_port,
        user,
        password,
        False,
        limit,
    ):

        list_of_list = []
        for i, code in df["sourcecode"].iteritems():
            list_of_list.append(preprocess_text(code))

        ft_model.build_vocab(sentences=list_of_list, update=(not first_iter))
        ft_model.train(
            sentences=list_of_list, total_examples=len(list_of_list), epochs=100
        )
        first_iter = False

    save_facebook_model(ft_model, "fasttext.model")


def get_embedding(df, embedding_size=32):

    ft_model = load_facebook_vectors("fasttext.model")

    list_of_AV = []

    for code in df["sourcecode"]:
        code = preprocess_text(code)
        AV = np.zeros(embedding_size)
        for word in code:
            emb = ft_model.wv[word]
            AV += emb
        AV /= len(AV)
        list_of_AV.append(AV)

    return np.array(list_of_AV)


def find_clusters(df, X, eps=0.2, min_samples=2):
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
    return df.assign(group=clustering.labels_), clustering


def store_data(df, col):
    pass


def get_similarity(with_data, user_db_port, user, password):

    train_embedding(with_data, user_db_port, user, password)

    df = get_data(with_data, user_db_port, user, password)
    # X = get_tfidf(df)
    X = get_embedding(df)
    del df["sourcecode"]
    df, clustering = find_clusters(df, X)

    with pd.option_context("display.max_rows", None, "display.max_columns", None):
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
