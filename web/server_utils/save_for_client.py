def save_column_to_json(df, column, filename, folder_path):
    """
    Saves an array of unique values from one chosen dataframe column to the file in json format.
    :param df: dataframe, data from which should be saved.
    :param column: name og the column, whose unique values should be saved.
    :param filename: name of the file for saving results.
    :param folder_path: path to the file for saving results.
    :return: None.
    """
    col_values = df.loc[:, column].unique().tolist()
    import json

    fullpath = folder_path + filename
    with open(fullpath, 'w', encoding='utf-8') as f:
        json.dump(sorted(col_values), f, ensure_ascii=False, indent=2)
