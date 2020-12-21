import pandas as pd
import numpy as np
import csv
import sys
csv.field_size_limit(sys.maxsize)

## Load DB CSV
df = pd.read_csv('wiki_pages_db.csv', header=None, names=['page_id','page_title','page_latest','dbname'],
                    dtype= {'page_id': int}, usecols=['page_id','dbname'])
df['dbname'] = df['dbname'].apply(lambda x: x[:-2])
db_map = pd.read_csv('wikipages.csv')
df = pd.merge(df, db_map, how='left', on='dbname')[['page_id','url']]
df['source'] = 'db'
del db_map

print('Loaded db data...')
print("Length of db pages:", len(df))

## load API CSV and delete duplicates
len_api = 0
uniq_api = 0
for df_api in pd.read_csv('wiki_pages_api.csv', header=None, names=['page_id' ,'page_title', 'url'], 
                         chunksize=500, dtype={'page_id':int}, usecols=['page_id','url']):
    df_api['source'] = 'api'
    len_api += len(df_api)
    df = pd.concat([df, df_api])
    df.drop_duplicates(subset=['page_id', 'url'], keep=False, inplace=True) # page titles do not match in API and db
    df_api = df[df['source']=='api']
    df = df[df['source']=='db']
    uniq_api += len(df_api)
    df_api.to_csv('comparison_api.csv', mode='a', header=False, index=False)

print('Loaded API data...')
print("Length of api pages:", len_api)

print("Length of unique pages in db:", len(df))
print("Length of unique pages in api:", uniq_api)

df.to_csv('comparison_db.csv', header=False, index=False)

print("Ok")

