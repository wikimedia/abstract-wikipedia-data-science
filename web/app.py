from flask import Flask, jsonify
from flask_cors import CORS

# configuration
DEBUG = True

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

# enable CORS
CORS(app)


# sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@app.route('/api/data', methods=['GET'])
def get_requested_data(weights, families, wikis):
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
            "dbname": "enwiktionary",
            "title": "C",
            "sourcecode": "CCCCCCCC",

        },
    ]
    test_data = [1, 2, 3]
    return jsonify({
        'status': 'success',
        'data': test_data
    })


if __name__ == '__main__':
    app.run()
