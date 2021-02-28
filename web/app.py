import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import pandas as pd

from web.server_utils.database_connections import get_sourcecode_from_database, \
    get_close_sourcecodes, get_titles_and_filters
from web.server_utils.scores_retrieval import get_score

# configuration
DEBUG = True

# set static files dir
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'client/dist')

# instantiate the app
app = Flask(__name__,
            # static_url_path='',
            # static_folder=static_file_dir,
            )
app.config.from_object(__name__)

# enable CORS
CORS(app)


# Main route, serve the web page, where you will import the js and css built files
@app.route('/')
def index():
    return send_from_directory(static_file_dir, 'index.html')


# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@app.route('/api/<wiki>/<id>')
def get_single_script_data(wiki, id):
    ser = get_sourcecode_from_database(wiki, id, 1147)

    if ser is None:
        return jsonify({
            'status': 'NotFound',
        })
    else:
        #cluster = get_close_sourcecodes(wiki, id, ser.loc['cluster'], 1147)
        test_vals = [
            ["kawiki", 376136, "მოდული:No globals"],
            ["bnwiki", 437245, "মডিউল:ক্রীড়া ছক/জয়-ড্র-হার "],
            ["enwiktionary", 5366907, "Module:Lydi-translit/testcases"],
            ["sowiki", 19126, "Module:WeatherBoxColors"],
            ["afwiktionary", 32943, "Module:redlink category"],
            ["fjwiki", 8468, "Module:String"],
        ]
        cluster = pd.DataFrame(test_vals, columns=["dbname", "pageid", "title"])
        if cluster is not None:
            cluster = cluster.to_json(orient='index')
            print(cluster)
        return jsonify({
            'status': 'success',
            'data': ser.to_json(),
            'cluster': cluster,
        })


@app.route('/api/data', methods=['GET'])
def get_requested_data():
    no_data = request.args.get('noData')
    chosen_families = request.args.getlist('chosenFamilies[]')
    # filter = request.args.get('filter', default='*', type=str)
    weights = request.args.getlist('weights[]', type=float)
    #print(no_data)
    #print(chosen_families)
    print(weights)

    df = get_score(weights=weights)
    data = df[['page_id', 'dbname']].head(50)
    data = get_titles_and_filters(data, 1147)
    more_data = data.to_json(orient='index')

    # test_data = [1, 2, 3]
    return jsonify({
        'status': 'success',
        'data': more_data
    })


if __name__ == '__main__':
    app.run()
