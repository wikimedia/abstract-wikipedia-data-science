## imports
import sys
import mwapi
import toolforge
import pandas as pd

## define constants
MIN_IDX = 0
MAX_IDX = 8 ## UPDATE WITH REAL VALUE
NAMESPACES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 
    90, 91, 92, 93, 100, 101, 102, 103, 104, 105, 106, 107, 486, 487, 
    828, 829, 1198, 1199, 2300, 2301, 2302, 2303, 2600, 5500, 5501]

def get_wiki_list(filename, start_idx, end_idx):
    ## List the wikis in the rage [start_idx, end_idx] and run function
    wikis = []
    with open(filename) as file:
        for i, line in enumerate(file):
            if i>=start_idx:
                wikis.append(line.strip(' \n'))
            if i==end_idx:
                break
    return wikis

def save_content(wiki, ns, data_list, missed):
    data_df = pd.DataFrame(data_list, columns=['id', 'title', 'url', 'length', 'content', 'format', 'model', 'touched'])
    data_df['wiki'] = wiki
    data_df['ns'] = ns
    data_df.to_csv('wiki_contents.csv', mode='a', header=False, index=False)

    missed_df = pd.DataFrame(missed, columns=['title', 'pageid'])
    missed_df['wiki'] = wiki
    missed_df['ns'] = ns
    missed_df.to_csv('missed_wiki_contents.csv', mode='a', header=False, index=False)

def get_contents(wikis):
    user_agent = toolforge.set_user_agent('test-tool-aisha')
    for wiki in wikis:
        session = mwapi.Session(wiki, user_agent=user_agent)
        for ns in NAMESPACES:
            data_list = []
            missed = []
            _gapcontinue = ''
            _continue = ''

            while True:
                params = {'action':'query',
                        'generator':'allpages',
                        'gapnamespace':ns,
                        'gaplimit':'max',
                        'format':'json',
                        'prop':'info',
                        'inprop':'url',
                        'gapcontinue': _gapcontinue,
                        'continue': _continue,
                        }
                
                result = session.get(params)

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
                        
                        data_list.append([pageid, title, url, length, content, content_format, content_model, touched])
                    except:
                        if ('title' in page.keys()) and ('pageid' in page.keys()):
                            missed.append([page['title'], page['pageid']])
                try:
                    _continue = result['continue']['continue']
                    _gapcontinue = result['continue']['gapcontinue'] \
                        if 'gapcontinue' in  result['continue'] else ''
                except:
                    break
                
                # print(len(data_list), 'pages loaded...')

            print("All pages loaded for %s in namespace %d. Missed: %d, Loaded: %d" \
                %(wiki, ns, len(missed), len(data_list)))

            save_content(wiki, ns, data_list, missed)
    
    print("Done loading!")

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
    
    if start_idx<MIN_IDX or end_idx<MIN_IDX or start_idx>MAX_IDX or end_idx>MAX_IDX:
        print("Error: Both indices should be in the range %d to %d." %(MIN_IDX, MAX_IDX))
        sys.exit()

    if start_idx>end_idx:
        print("Error: ending index must be greater than start index.")
        sys.exit()
    
    wikis = get_wiki_list('wikipages.txt', start_idx, end_idx)
    get_contents(wikis)
    