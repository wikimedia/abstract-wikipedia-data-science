import pandas as pd
import numpy as np
import re
import argparse
from sklearn.cluster import OPTICS
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


def preprocess_text(document):
    pat = r"(?u)\w\w+|[^\w\s]+"
    return re.findall(pat, document)


def train_embedding(
    is_word,
    user_db_port,
    user,
    password,
    limit=10000,
    maxlen=20000,
    embedding_size=32,
):
    if is_word:
        model = FastText(
            size=embedding_size,
            window=5,
            min_count=5,
            max_vocab_size=60000,
            sg=1,  # skip-gram
        )
    else:
        model = Doc2Vec(
            vector_size=embedding_size,
            window=5,
            min_count=5,
            max_vocab_size=60000,
        )

    query = "SELECT page_id, dbname, LEFT(sourcecode, %s) FROM Scripts" % maxlen

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


def get_embedding(df, is_word):

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


def find_clusters(df, X):
    clustering = OPTICS(
        max_eps=np.inf,
        min_samples=5,
        metric="minkowski",
        algorithm="auto",
        cluster_method="xi",
        n_jobs=-1,
    ).fit(X)
    return df.assign(group=clustering.labels_), clustering


def store_data(df, col, user_db_port, user, password):

    query1 = "UPDATE Scripts SET " + col + "=NULL"
    query2 = "UPDATE Scripts SET " + col + "=%s WHERE page_id=%s AND dbname=%s"
    max_tries = 3
    retry_counter = 1

    while True:
        try:
            ## Need to keep query1 and query2 in the same transaction
            conn = db_acc.connect_to_user_database(
                DATABASE_NAME, user_db_port, user, password
            )
            with conn.cursor() as cur:
                cur.execute(query1)
                for _, elem in df.iterrows():
                    cur.execute(
                        query2, [elem["group"], elem["page_id"], elem["dbname"]]
                    )
            conn.commit()
            close_conn(conn)
            break
        except (pymysql.err.DatabaseError, pymysql.err.OperationalError) as err:
            close_conn(conn)
            if retry_counter == max_tries:
                raise Exception(err)
            print("Retrying saving clusters in 1 minute...")
            retry_counter += 1
            time.sleep(60)
        except Exception as err:
            print("Something went wrong. Error saving clusters \n", repr(err))
            break


def get_similarity(
    with_data, train_model, word_embedding, user_db_port, user, password
):

    if train_model:
        train_embedding(word_embedding, user_db_port, user, password)

    df = get_data(with_data, user_db_port, user, password)
    X = get_embedding(df, word_embedding)
    del df["sourcecode"]
    df, clustering = find_clusters(df, X)

    col = "cluster" if with_data else "cluster_wo_data"
    store_data(df, col, user_db_port, user, password)


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
    parser.add_argument(
        "--train-model",
        "-tr",
        action="store_true",
        help="Whether to train the embedding model. If not set, will use saved models.",
    )
    parser.add_argument(
        "--word-embedding",
        "-we",
        action="store_true",
        help="Whether to use word embedding (FastText). If not set, doc2vec will be used.",
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
    get_similarity(
        args.with_data,
        args.train_model,
        args.word_embedding,
        args.user_db_port,
        args.user,
        args.password,
    )
