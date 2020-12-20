import pandas as pd
import numpy as np
import csv
import sys
csv.field_size_limit(sys.maxsize)

## Load DB CSV
df = pd.read_csv('wiki_pages_db.csv', header=None, names=['page_id','page_title','page_latest','dbname'],
                    dtype= {'page_id': int}, usecols=['page_id','page_title','dbname'])
df['dbname'] = df['dbname'].apply(lambda x: x[:-2])
db_map = pd.read_csv('wikipages.csv')
df = pd.merge(df, db_map, how='left', on='dbname')[['page_id', 'page_title', 'url']]
df['source'] = 'db'
del db_map

print('Loaded db data...')
print("Length of db pages:", len(df))

## load API CSV and delete duplicates
len_api = 0
for df_api in pd.read_csv('wiki_pages_api.csv', header=None, names=['page_id','page_title','url'], dtype= {'page_id': int}, chunksize=10):
    df_api['source'] = 'api'
    len_api += len(df_api)
    df = pd.concat([df, df_api])
    df = df[~df.duplicated(subset=['page_id', 'page_title', 'url'], keep=False)]

print('Loaded API data...')
print("Length of api pages:", len_api)

print("Length of unique pages:", len(df))
print("Length of unique pages in db:", len(df[df['source']=='db']))
print("Length of unique pages in api:", len(df[df['source']=='api']))

df.to_csv('comparison.csv')

print("Ok")

