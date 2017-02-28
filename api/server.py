from buku import BukuDb
from flask import Flask, jsonify, request


bukudb = BukuDb()

app = Flask(__name__)


@app.route('/api/tags', methods=['GET'])
def get_tags():
    tags = bukudb.get_tag_all()
    result = {
        'tags': tags[0]
    }
    return jsonify(result)


@app.route('/api/bookmarks', methods=['GET', 'POST'])
def bookmarks():
    if request.method == 'GET':
        bookmarks = bukudb.get_rec_all()
        result = {
            'bookmarks': []
        }
        for bookmark in bookmarks:
            result_bookmark = {
                'url': bookmark[1],
                'title': bookmark[2],
                'tags': list(filter(None, bookmark[3].split(','))),
                'description': bookmark[4]
            }
            result['bookmarks'].append(result_bookmark)
        return jsonify(result)
    elif request.method == 'POST':
        result_flag = bukudb.add_rec(request.form['url'], request.form['title'],
                                     request.form['tags'], request.form['description'])
        if result_flag:
            return jsonify({'status': 0, 'message': 'success'}), 200, {'ContentType': 'application/json'}
        else:
            return jsonify({'status': 1, 'message': 'failure'}), 400, {'ContentType': 'application/json'}

@app.route('/api/bookmarks/<id>', methods=['GET', 'PUT', 'DELETE'])
def bookmark_api(id):
    try:
        id = int(id)
    except ValueError:
        return jsonify({'status': 1, 'message': 'failure'}), 400, {'ContentType': 'application/json'}
    if request.method == 'GET':
        bookmark = bukudb.get_rec_by_id(id)
        if bookmark is not None:
            result = {
                'url': bookmark[1],
                'title': bookmark[2],
                'tags': list(filter(None, bookmark[3].split(','))),
                'description': bookmark[4]
            }
            return jsonify(result)
        else:
            return jsonify({'status': 1, 'message': 'failure'}), 400, {'ContentType': 'application/json'}
    elif request.method == 'PUT':
        result_flag = bukudb.update_rec(id, request.form['url'], request.form.get('title'),
                                        request.form['tags'], request.form['description'])
        if result_flag:
            return jsonify({'status': 0, 'message': 'success'}), 200, {'ContentType': 'application/json'}
        else:
            return jsonify({'status': 1, 'message': 'failure'}), 400, {'ContentType': 'application/json'}
    else:
        result_flag = bukudb.delete_rec(id)
        if result_flag:
            return jsonify({'status': 0, 'message': 'success'}), 200, {'ContentType': 'application/json'}
        else:
            return jsonify({'status': 1, 'message': 'failure'}), 400, {'ContentType': 'application/json'}

def run():
    app.run(debug=True)

run()
