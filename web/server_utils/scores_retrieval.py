import pandas as pd
import sys
from pathlib import Path
import re


def filter_families(df, families_list):

    SPECIAL_WIKIS_LIST = [
        "apiportalwiki",
        "commonswiki",
        "donatewiki",
        "foundationwiki",
        "incubatorwiki",
        "loginwiki",
        "mediawikiwiki",
        "metawiki",
        "nostalgiawiki",
        "outreachwiki",
        "sourceswiki",
        "specieswiki",
        "testcommonswiki",
        "thankyouwiki",
        "votewiki"
    ]
    if "wikipedia" in families_list:
        families_list.append("wiki")
        families_list.remove("wikipedia")


    to_drop = []
    for i in range(df.shape[0]):
        found = False
        curr_dbname = df.loc[i, 'dbname']
        if curr_dbname in SPECIAL_WIKIS_LIST:
            if "special" in families_list:
                found = True
        else:
            for elem in families_list:
                check_entry = re.match(r"\S+" + elem + "$", curr_dbname)
                if check_entry:
                    found = True
                    break
        if not found:
            to_drop.append(i)

    df = df.drop(to_drop, axis=0)
    return df


def filter_families_with_linkage(df, linkage_df, chosen_families_list):
    to_drop = []
    for i in range(df.shape[0]):
        curr_dbname = df.loc[i, 'dbname']
        curr_family = linkage_df[(linkage_df['dbname'] == curr_dbname)]['family'].tolist()
        if curr_family[0] not in chosen_families_list:
            to_drop.append(i)

    df = df.drop(to_drop, axis=0)
    return df


def filter_data_modules(df):
    print(df.loc[df['is_data'] == 0])
    return df.loc[df['is_data'] == 0]


def get_score(
    csv_address=str(Path.home())+'/abstract-wikipedia-data-science/data_distribution.csv',
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
    df = pd.read_csv(csv_address)
    weights = [w / sum(weights) for w in weights]  ## Normalize weights
    df["score"] = df[feature_names].dot(weights)
    return df.sort_values(by=["score"], ascending=False)


if __name__ == "__main__":
    res = get_score()

    print(res.sort_values(by=["score"], ascending=False))