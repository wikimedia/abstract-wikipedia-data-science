## imports
import sys
import mwapi
import toolforge
import pandas as pd

## define constants
MIN_IDX = 0

def get_wiki_list(filename, start_idx, end_idx):
    ## List the wikis in the rage [start_idx, end_idx] and run function
    df = pd.read_csv(filename)
    wikis = df['url'].values
    return wikis[start_idx:end_idx+1]

def save_content(wiki, data_list, missed):
    ## consider using `chunksize` if required

    data_df = pd.DataFrame(data_list, columns=['id', 'title', 'url', 'length', 'content', 'format', 'model', 'touched'])
    data_df['wiki'] = wiki
    data_df.to_csv('wiki_contents.csv', mode='a', header=False, index=False)

    missed_df = pd.DataFrame(missed, columns=['title', 'pageid'])
    missed_df['wiki'] = wiki
    missed_df.to_csv('missed_wiki_contents.csv', mode='a', header=False, index=False)

def get_contents(wikis):
    '''
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
            print("Failed to connect to ", wiki, "\n", e)
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
                print("Could not GET ", wiki, "\n", e)
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
                    except:
                        if ('title' in page.keys()) and ('pageid' in page.keys()):
                            if ('lastrevid' in page.keys()) and (revid != 0):
                                missed.append([page['title'], page['pageid']])
            
                cnt_data_list += len(data_list)
                cnt_missed += len(missed)
                save_content(wiki, data_list, missed)
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

def get_missed_contents(filename='missed_wiki_contents.csv'):
    pass

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
    
    if start_idx<MIN_IDX or end_idx<MIN_IDX:
        print("Error: Indices should be %d or more." %MIN_IDX)
        sys.exit()

    if start_idx>end_idx:
        print("Error: Ending index must be greater than start index.")
        sys.exit()
    
    wikis = get_wiki_list('wikipages.csv', start_idx, end_idx)
    get_contents(wikis)
    