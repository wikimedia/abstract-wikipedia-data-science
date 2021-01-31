import toolforge
import pandas as pd
import pymysql
import numpy as np

import edlib
from polyleven import levenshtein as lev_dist

from sklearn.cluster import DBSCAN

import constants


def generate_distance_matrix(df):
    dam_lev = []

    len_arr = df['sourcecode'].nunique()

    for i in range(len_arr):
        dam_lev.append([0] * len_arr)

    good = bad = 0
    for i in range(len_arr):
        for j in range(i, len_arr):
            if i != j:
                sum_len = df.iloc[i]['length'] + df.iloc[i]['length']
                try:
                    dam_lev[j][i] = dam_lev[i][j] = np.round(edlib.align(
                        df.iloc[i]['sourcecode'], df.iloc[j]['sourcecode'])['editDistance'] / sum_len, 6)
                    good += 1
                except (UnicodeEncodeError, ValueError):
                    # ValueError if more than 256 unique character in both texts (edlib limitation)
                    # UnicodeEncodeError because conversion from Python to C++ for edlib works only for Unicode
                    dam_lev[j][i] = dam_lev[i][j] = np.round(lev_dist(
                        df.iloc[i]['sourcecode'], df.iloc[j]['sourcecode']) / sum_len, 6)
                    bad += 1
                except Exception as e:
                    print('Error while generating distance matrix: ', e)
    return dam_lev


def levenshtein_clasterization(df):
    dam_lev = generate_distance_matrix(df)
    clustering = DBSCAN(
        eps=constants.ANALYSIS_CLUSTERING_EPS,
        min_samples=1,
        metric='precomputed').fit(dam_lev)
    labels = clustering.labels_
    res = df.assign(group=labels)

    return res

