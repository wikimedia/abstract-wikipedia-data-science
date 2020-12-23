## imports
import sys
import mwapi
import toolforge
import pandas as pd
import pymysql
import datetime


## define constants
MIN_IDX = 0
DATABASE_NAME = 's54588__data'


def _get_wiki_list(start_idx, end_idx):
    wikis = []
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("select url from Sources where url is not NULL")  # all, except 'meta'
            for wiki in cur:
                wikis.append(wiki[0])
        return wikis[start_idx:end_idx + 1]
    except pymysql.err.OperationalError:
        print('Wikiprojects update checker: failure, please use only in Toolforge environment')
        exit(1)


def get_wiki_list(filename, start_idx, end_idx):
    ## List the wikis in the rage [start_idx, end_idx] and run function
    df = pd.read_csv(filename)
    wikis = df['url'].values
    return wikis[start_idx:end_idx+1]


def _save_content(wiki, data_list, missed, step=1):
    # data_list.append([pageid, title, url, length, content, content_format, content_model, touched])
    data_df = pd.DataFrame(data_list, columns=['id', 'title', 'url', 'length', 'content', 'format', 'model', 'touched'])

    query = ("insert into Scripts(dbname, page_id, title, sourcecode, touched, in_api) "
             "             values(%s, %s, %s, %s, %s, %s)\n"
             "on duplicate key update in_api = %s"
             )
    try:
        conn = toolforge.toolsdb(DATABASE_NAME)
        with conn.cursor() as cur:
            cur.execute("select dbname from Sources where url = %s", wiki)
            dbname = cur.fetchone()[0]
            for index, elem in data_df.iterrows():
                time = elem['touched'].replace('T', ' ').replace('Z', ' ')
                cur.execute(query,
                            [dbname, elem['id'], elem['title'], elem['content'], time, 1, 1])
        conn.commit()
        conn.close()
    except pymysql.err.OperationalError as err:
        print(err)
        exit(1)



def save_content(wiki, data_list, missed, step=1):
    ## consider using `chunksize` if required

    data_df = pd.DataFrame(data_list, columns=['id', 'title', 'url', 'length', 'content', 'format', 'model', 'touched'])
    data_df['wiki'] = wiki
    data_df.to_csv('wiki_contents.csv', mode='a', header=False, index=False)

    data_df[['id', 'title', 'wiki']].to_csv('wiki_pages_api.csv', mode='a', header=False, index=False)

    missed_df = pd.DataFrame(missed, columns=['title', 'pageid'])
    missed_df['wiki'] = wiki
    missed_df['step'] = step
    missed_df.to_csv('missed_wiki_contents.csv', mode='a', header=False, index=False)

def needs_update(wiki, pageid, title, touched, revid):
    return True

def get_contents(wikis, revise=False):
    '''
    revise: `False` collects all contents and saves fresh
            `True` only collects those edits

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
                    'gaplimit':'max',
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
                            content_format = content_info['contentformat']
                            
                            if content_model=='Scribunto':
                                data_list.append([pageid, title, url, length, content, content_format, content_model, touched])
                    except Exception as e:
                        if ('title' in page.keys()) and ('pageid' in page.keys()):
                            missed.append([pageid, title])
                            print("Miss:", wiki, title, pageid, e)
            
                cnt_data_list += len(data_list)
                cnt_missed += len(missed)
                save_content(wiki, data_list, missed)
                _save_content(wiki, data_list, missed)
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


def get_missed_contents(wikis, filename='missed_wiki_contents.csv'):

    df = pd.read_csv(filename, names=['pageid', 'title', 'wiki', 'step'])
    df = df[df.wiki.isin(wikis) & df.step==1]
    user_agent = toolforge.set_user_agent('abstract-wiki-ds')
    print("Started loading missed contents...")

    for wiki, w_df in df.groupby('wiki'):
        try:
            session = mwapi.Session(wiki, user_agent=user_agent)
        except Exception as e:
            print("Failed to connect to", wiki, "\n", e)
            continue
            
        pageids = w_df['pageid'].values
        titles = w_df['title'].values
        data_list = []
        missed = []
        
        for pageid, title in zip(list(pageids), titles):
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
                    length = page['length']
                    content_info = page['revisions'][0]['slots']['main']
                    content = content_info['content']
                    content_format = content_info['contentformat']
                    content_model = content_info['contentmodel']
                    touched = page['touched']
                    data_list.append([pageid, title, url, length, content, content_format, content_model, touched])
            except Exception as e:
                missed.append([pageid, title])
                print("Miss:", pageid, "from wiki:", wiki, "\n", e)

        save_content(wiki, data_list, missed, 2)
        _save_content(wiki, data_list, missed, 2)
        print("All pages loaded for %s. Missed: %d, Loaded: %d" \
            %(wiki, len(missed), len(data_list)))

    print("Done loading missed pages!")

if __name__ == "__main__":
    
    ## Check arguments for errors
    if len(sys.argv)<3:
        print("Error: Two args required: start and end index. E.g python3 fetch_content.py 1 8.")
        sys.exit()
    
    try:
        start_idx = int(sys.argv[1])
        end_idx = int(sys.argv[2])
    except:
        print("Error: Both indices should be integer.")
        sys.exit()
    
    ## Check for optional revise argument
    revise = False
    try:
        revise = sys.argv[3].lower() in ['true', 'yes', 'y', 't']
    except:
        pass
    
    if start_idx<MIN_IDX or end_idx<MIN_IDX:
        print("Error: Indices should be %d or more." %MIN_IDX)
        sys.exit()

    if start_idx>end_idx:
        print("Error: Ending index must be greater than start index.")
        sys.exit()
    
    wikis = _get_wiki_list(start_idx, end_idx)
    get_contents(wikis)
    get_missed_contents(wikis=wikis)
    
