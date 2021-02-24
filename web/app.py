import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# configuration
DEBUG = True

# set static files dir
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'client/dist')

# instantiate the app
app = Flask(__name__,
            static_url_path='',
            static_folder=static_file_dir,
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
    test_script = ("")
    test_data = {
        "pageid": id,
        "dbname": wiki,
        "title": 'TESTPAGE',
        "sourcecode": ("SOME TEST CODE GOES IN THERE\n"
                       " AND A BIT MORE LINES"),
        "similarItems": []

    }

    return jsonify({
        'status': 'success',
        'data': test_data
    })


@app.route('/api/data', methods=['GET'])
def get_requested_data():
    no_data = request.args.get('noData')
    chosen_families = request.args.getlist('chosenFamilies[]')
    # filter = request.args.get('filter', default='*', type=str)
    print(no_data)
    print(chosen_families)

    test_data = [
        {
            "pageid": 1,
            "dbname": "enwiki",
            "title": "A",
            "sourcecode": "AAAAAAA",

        },
        {
            "pageid": 2,
            "dbname": "ruwiki",
            "title": "B",
            "sourcecode": "BBBBB",

        },
        {
            "pageid": 3,
            "dbname": "enwiktionary ",
            "title": "C",
            "sourcecode": "CCCCCCCC",

        },
    ]
    # test_data = [1, 2, 3]
    return jsonify({
        'status': 'success',
        'data': test_data
    })


if __name__ == '__main__':
    app.run()
