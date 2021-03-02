def save_column_to_json(df, column, filename, folder_path):
    col_values = df.loc[:, column].unique().tolist()
    import json

    fullpath = folder_path + filename
    with open(fullpath, 'w', encoding='utf-8') as f:
        json.dump(sorted(col_values), f, ensure_ascii=False, indent=2)
