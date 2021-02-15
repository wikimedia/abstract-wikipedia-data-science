import pandas as pd
import numpy as np
import re
import argparse
import random
from scipy.sparse import vstack
from sklearn.cluster import DBSCAN, KMeans, OPTICS
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.models.fasttext import FastText
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
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
    is_word=True,
):
    if is_word:
        model = FastText(
            size=embedding_size,
            window=5,
            min_count=5,
            max_vocab_size=60000,
            sg=1,
        )
    else:
        model = Doc2Vec(
            vector_size=embedding_size,
            window=5,
            min_count=5,
            max_vocab_size=60000,
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
            if is_word:
                list_of_list.append(preprocess_text(code))
            else:
                list_of_list.append(TaggedDocument(preprocess_text(code), [i]))

        if is_word:
            model.build_vocab(sentences=list_of_list, update=(not first_iter))
            model.train(
                sentences=list_of_list, total_examples=len(list_of_list), epochs=10
            )
        else:
            model.build_vocab(documents=list_of_list, update=(not first_iter))
            model.train(
                documents=list_of_list, total_examples=len(list_of_list), epochs=10
            )

        first_iter = False

    if is_word:
        model.save("fasttext.model")
    else:
        model.save("doc2vec.model")


def get_embedding(df, is_word=True):

    if is_word:
        model = FastText.load("fasttext.model")
    else:
        model = Doc2Vec.load("doc2vec.model")

    def get_emb(sent):
        if is_word:
            AV = np.zeros(model.vector_size)
            for word in sent:
                AV += model.wv[word]
            AV /= len(AV)
            return AV
        else:
            return model.infer_vector(sent)

    list_of_embeddings = []

    for code in df["sourcecode"]:
        list_of_embeddings.append(get_emb(preprocess_text(code)))

    return np.array(list_of_embeddings)


def find_clusters(df, X, eps=0.2, min_samples=2):
    # clustering = DBSCAN(eps=eps, min_samples=min_samples, algorithm="kd_tree").fit(X)
    clustering = OPTICS(
        max_eps=np.inf,
        min_samples=5,
        metric="minkowski",
        algorithm="auto",
        cluster_method="xi",
        n_jobs=-1,
    ).fit(X)
    ##try cosine and dbscan, algorithm=kd_tree
    # clustering = KMeans(n_clusters=100).fit(X)
    return df.assign(group=clustering.labels_), clustering


def store_data(df, col):
    pass


def get_similarity(with_data, user_db_port, user, password):

    # train_embedding(with_data, user_db_port, user, password, is_word=False)

    df = get_data(with_data, user_db_port, user, password)
    # X = get_tfidf(df)
    X = get_embedding(df, is_word=False)
    del df["sourcecode"]
    df, clustering = find_clusters(df, X)
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(df.groupby("group").agg({"page_id": "count"}))

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
