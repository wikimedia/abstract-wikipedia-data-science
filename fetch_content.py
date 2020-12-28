## imports
import sys
import mwapi
import toolforge
import pandas as pd
import pymysql
import numpy as np
import argparse


pymysql.converters.encoders[np.int64] = pymysql.converters.escape_int
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)


## define constants
MIN_IDX = 0
DATABASE_NAME = 's54588__data'


def get_wiki_list(start_idx, end_idx):
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("select url from Sources where url is not NULL")  # all, except 'meta'
            ret = [wiki[0] for wiki in cur][start_idx:end_idx + 1]
        conn.close()
        return ret
    except pymysql.err.OperationalError:
        print('Failure: please use only in Toolforge environment')
        exit(1)


def save_content(wiki, data_list, in_api, in_database):

    data_df = pd.DataFrame(data_list, columns=['id', 'title', 'url', 'length', 'content', 'content_model', 'touched', 'lastrevid'])

    query = ("insert into Scripts(dbname, page_id, title, sourcecode, touched, in_api, in_database, length, content_model, lastrevid, url) "
             "             values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\n"
             "on duplicate key update title = %s, sourcecode = %s, touched = %s, in_api = %s, in_database = %s,"
             "length = %s, content_model = %s, lastrevid = %s, url = %s, is_missed=%s"
             )
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("select dbname from Sources where url = %s", wiki)
            dbname = cur.fetchone()[0]
            for index, elem in data_df.iterrows():
                time = elem['touched'].replace('T', ' ').replace('Z', ' ')
                cur.execute(query,
                            [dbname, elem['id'], 
                            elem['title'], elem['content'], time, in_api, in_database, elem['length'], elem['content_model'], elem['lastrevid'], elem['url'],
                            elem['title'], elem['content'], time, in_api, in_database, elem['length'], elem['content_model'], elem['lastrevid'], elem['url'], 0])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)
    except Exception as err:
        print('Error saving pages from',wiki)
        print(err)


def save_missed_content(wiki, missed):

    missed_df = pd.DataFrame(missed, columns=['id'])

    query = ("insert into Scripts(dbname, page_id, in_api, is_missed) "
             "             values(%s, %s, %s, %s)\n"
             "on duplicate key update in_api = %s, is_missed = %s"
             )
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("select dbname from Sources where url = %s", wiki)
            dbname = cur.fetchone()[0]
            for index, elem in missed_df.iterrows():
                cur.execute(query,
                            [dbname, elem['id'], 1, 1, 1, 1])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)


def needs_update(wiki, pageid, title, touched, revid):
    return True


def get_contents(wikis, revise=False):
    '''
    revise: `False` collects all contents and saves fresh
            `True` only collects those that have been edited

    Possible ways for the process to fail:
    1. Failed to connect to wiki (See from output)
    2. Connected but could not GET wiki (See from output)
    3. Could not grab a page (Listed in missed pages)
    '''
    user_agent = toolforge.set_user_agent('abstract-wiki-ds')
    for wiki in wikis:
        try:
            session = mwapi.Session(wiki, user_agent=user_agent)
        except Exception as e:
            print("Failed to connect to", wiki, "\n", e)
            continue

        data_list = []
        cnt_data_list = 0
        missed = []
        cnt_missed = 0
        _gapcontinue = ''
        _continue = ''

        while True:
            params = {'action':'query',
                    'generator':'allpages',
                    'gapnamespace':828,
                    'gaplimit':300,
                    'format':'json',
                    'prop':'info',
                    'inprop':'url',
                    'gapcontinue': _gapcontinue,
                    'continue': _continue,
                    }
            
            try:
                result = session.get(params)
            except Exception as e:
                print("Could not GET", wiki, "\n", e)
                break
            
            if 'query' in result.keys():
                for page in list(result['query']['pages'].values()):
                    try:
                        pageid = page['pageid']
                        title = page['title']
                        touched = page['touched']
                        length = page['length']
                        url = page['fullurl']
                        revid = page['lastrevid']
                        
                        if (not revise) or needs_update(wiki, pageid, title, touched, revid):
                            params = {'action':'query',
                                    'format':'json',
                                    'prop':'revisions',
                                    'revids':revid,
                                    'rvprop':'content',
                                    'rvslots':'main',
                                    'formatversion':2
                                    }
                    
                            rev_result = session.get(params)

                            content_info = rev_result['query']['pages'][0]['revisions'][0]['slots']['main']
                            content = content_info['content']
                            content_model = content_info['contentmodel']
                            
                            if content_model=='Scribunto':
                                data_list.append([pageid, title, url, length, content, content_model, touched, revid])
                    except Exception as err:
                        if 'pageid' in page.keys():
                            missed.append([pageid])
                            print("Miss:", wiki, title, pageid, "\n" ,err)
            
                cnt_data_list += len(data_list)
                cnt_missed += len(missed)
                save_missed_content(wiki, missed)
                save_content(wiki, data_list, 1, 0)
                print(cnt_data_list, 'pages loaded...')
                data_list, missed = [], []

            try:
                _continue = result['continue']['continue']
                _gapcontinue = result['continue']['gapcontinue'] if 'gapcontinue' in  result['continue'] else ''
            except:
                break

        print("All pages loaded for %s. Missed: %d, Loaded: %d" \
            %(wiki, cnt_missed, cnt_data_list))
    
    print("Done loading!")


def get_db_map(wikis=[], dbs=[]):
    
    query_input = []
    
    if len(wikis)>0:
        placeholders = ','.join('%s' for _ in wikis)
        query_input = wikis
        query = ("select dbname, url from Sources where url in (%s)" % placeholders)
    else:
        placeholders = ','.join('%s' for _ in dbs)
        query_input = dbs
        query = ("select dbname, url from Sources where dbname in (%s)" % placeholders)
    
    db_map = {}

    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute(query,query_input)
            db_map = {data[0]:data[1] for data in cur}
        conn.close()
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)
    
    return db_map, placeholders


def get_pages(df, in_api, in_database):
    '''
    df columns: page_id, dbname, wiki
    dbname not required
    '''
    user_agent = toolforge.set_user_agent('abstract-wiki-ds')
    for wiki, w_df in df.groupby('wiki'):
        try:
            session = mwapi.Session(wiki, user_agent=user_agent)
        except Exception as e:
            print("Failed to connect to", wiki, "\n", e)
            continue
            
        pageids = w_df['page_id'].values
        data_list = []
        missed = []
        
        for pageid in list(pageids):
            params = {
                'action':'query',
                'format':'json',
                'prop':'revisions|info',
                'pageids':pageid,
                'rvprop':'content',
                'rvslots':'main',
                'inprop':'url',
                'formatversion':2
            }

            try:
                result = session.get(params)
                page = result['query']['pages'][0]
                if page['lastrevid']!=0:
                    url = page['fullurl']
                    title = page['title']
                    length = page['length']
                    content_info = page['revisions'][0]['slots']['main']
                    content = content_info['content']
                    content_model = content_info['contentmodel']
                    touched = page['touched']
                    revid = page['lastrevid']
                    
                    if content_model=='Scribunto':
                        data_list.append([pageid, title, url, length, content, content_model, touched, revid])
            except Exception as err:
                missed.append([pageid])
                print("Miss:", pageid, "from wiki:", wiki, "\n", err)

        save_content(wiki, data_list, in_api, in_database)
        save_missed_content(wiki, missed)
        print("All pages loaded for %s. Missed: %d, Loaded: %d" \
            %(wiki, len(missed), len(data_list)))


def get_missed_contents(wikis):

    print("Started loading missed contents...")

    db_map, placeholders = get_db_map(wikis=wikis)
    query = ("select page_id, dbname from Scripts where dbname in (%s) and in_api=1 and is_missed=1" % placeholders)
    
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute(query, list(db_map.keys()))
            df = pd.DataFrame(cur, columns=['page_id', 'dbname'])
        conn.close()
    except pymysql.err.OperationalError as err:
        print('Failure: please use only in Toolforge environment')
        exit(1)

    df['wiki'] = df['dbname'].map(db_map)
    get_pages(df, 1, 0)
    print("Done loading missed pages!")


def index_type(x):
    x = int(x)
    if x < MIN_IDX:
        raise argparse.ArgumentError("Minimum index is 0")
    return x


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Updates Lua scripts and their additional info in database in Toolforge, "
                    "fetching info from Wikimedia API. For testing and parallelization sake, use start-idx and end-idx "
                    "parameters to choose which wikis from Sources table will be worked with."
                    "To use from local PC, use flag --local and all the additional flags needed for "
                    "establishing connection through ssh tunneling."
                    "More help available at "
                    "https://wikitech.wikimedia.org/wiki/Help:Toolforge/Database#SSH_tunneling_for_local_testing_which_makes_use_of_Wiki_Replica_databases"
    )
    parser.add_argument("start-idx", type=index_type,
                        help="Starting index of info, fetched from database Sources, sorted by key.")
    parser.add_argument("end-idx", type=index_type,
                        help="Ending index of info, fetched from database Sources, sorted by key.")
    parser.add_argument("--revise", "-rev", action="store_true",
                        help="Whether content should be revised.")

    parser.add_argument("--local", "-l", action="store_true",
                        help="Connection is initiated from local pc.")
    local_data = parser.add_argument_group(title="Info for connecting to Toolforge from local pc.")
    local_data.add_argument("--replicas-port", "-r", type=int,
                            help="Port for connecting to meta table through ssh tunneling, if used.")
    local_data.add_argument("--user-db-port", "-udb", type=int,
                            help="Port for connecting to tables, created by user in Toolforge, "
                                 "through ssh tunneling, if used.")
    local_data.add_argument("--user", "-u", type=str,
                            help="Toolforge username of the tool.")
    local_data.add_argument("--password", "-p", type=str,
                            help="Toolforge password of the tool.")
    args = parser.parse_args()

    if args.start_idx > args.end_idx:
        sys.exit("Error: Ending index must be greater than start index.")

    if not args.local:
        wikis = get_wiki_list(args.start_idx, args.end_idx)
        get_contents(wikis)
        get_missed_contents(wikis=wikis)
    else:
        pass
