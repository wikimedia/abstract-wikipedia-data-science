import pandas as pd
import sys
from pathlib import Path


def filter_families_with_linkage(df, linkage_df, chosen_families_list):
    """
    Leaves in dataframe only entries, where the project family of the wiki was checked by user.
    :param df: dataframe with data on scripts, fetched from csv file.
    :param linkage_df: dataframe, containing linkage between name of the wiki and its project family.
    :param chosen_families_list: list of the project families, defining entries from which wikis
    should be left in the dataframe.
    :return: pandas.DataFrame.
    """
    dbs = linkage_df[linkage_df['family'].isin(chosen_families_list)]['dbname']
    df = df[df['dbname'].isin(dbs)]
    return df


def filter_languages_with_linkage(df, linkage_df, chosen_langs_list):
    """
    Leaves in dataframe only entries, where the language of the wiki was checked by user.
    :param df: dataframe with data on scripts, fetched from csv file.
    :param linkage_df: dataframe, containing linkage between name of the wiki and its language.
    :param chosen_langs_list: list of the languages, defining entries from which wikis
    should be left in the dataframe.
    :return: pandas.DataFrame.
    """
    dbs = linkage_df[linkage_df['lang'].isin(chosen_langs_list)]['dbname']
    df = df[df['dbname'].isin(dbs)]
    return df


def filter_data_modules(df):
    """
    Removes entries from the DataFrame with scripts info which are marked as data.
    :param df: dataframe with data on scripts, fetched from csv file.
    :return: pandas.DataFrame.
    """
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

    :param csv_address: path and name of the csv file, where feature scores are stored.
    :param feature_names: Features against whom final score is to be calculated.
    :param weights: The linear weights to give to each feature.
    :return: pandas.DataFrame.
    """

    if (len(feature_names)) != len(weights):
        sys.exit("Number of features is not equal to the number of weights!")
    df = pd.read_csv(csv_address)
    weights = [w / sum(weights) for w in weights]           # Normalize weights
    df["score"] = df[feature_names].dot(weights)
    return df.sort_values(by=["score"], ascending=False)