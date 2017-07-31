from flask import Flask, jsonify
from flask import make_response
from flask import abort
from flask import request
from flask_httpauth import HTTPBasicAuth
import numpy as np
import requests
import config
from recalculation import create_hg, top_projection, scale

app = Flask(__name__)
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    r = requests.post('http://service.instatfootball.com/ws.php',
                      json={'server': "instatfootball.com",
                            'login': config.login,
                            'pass': config.password,
                            'proc': 'schedule_validate_user_by_login_pass',
                            'params':
                                {
                                    '@login': [username, 'in'],
                                    '@pass': [password, 'in']
                                }
                            })
    response = r.json()
    if not response['data']:
        return False
    return True


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)


@app.route('/api/v1.0/test', methods=['POST'])
@auth.login_required
def test():
    return 'Verification was successful'


@app.route('/api/v1.0/setcenter', methods=['POST'])
@auth.login_required
def set_center():
    if not request.json:
        abort(400)

    content = request.get_json(silent=True)
    xc = content['x']
    yc = content['y']

    np.savetxt('/home/pavel/scripts/restful/center', np.array([xc, yc]))

    return jsonify({'Successful':  True}), 201


@app.route('/api/v1.0/setcorners', methods=['POST'])
@auth.login_required
def set_corners():
    if not request.json:
        abort(400)
    content = request.get_json(silent=True)

    time = content['time']

    left_top = content['Left-top']
    xlt, ylt = left_top[0], left_top[1]

    right_top = content['Right-top']
    xrt, yrt = right_top[0], right_top[1]

    right_bottom = content['Right-bottom']
    xrb, yrb = right_bottom[0], right_bottom[1]

    left_bottom = content['Left-bottom']
    xlb, ylb = left_bottom[0], left_bottom[1]

    data = np.array([[time], [xlt, ylt], [xrt, yrt], [xrb, yrb], [xlb, ylb]])
    np.savetxt('/home/pavel/scripts/restful/corners', data)

    return jsonify({'Successful':  True}), 201


@app.route('/api/v1.0/recalculate', methods=['POST'])
@auth.login_required
def recalculation():
    if not request.json:
        abort(400)

    try:
        center = np.loadtxt('center', dtype=int)
    except FileNotFoundError:
        return jsonify({'Successful': False, 'Message': 'No data about the center'}), 428

    try:
        corners = np.loadtxt('corners', dtype=int)
    except FileExistsError:
        return jsonify({'Successful': False, 'Message': 'No data about the corners'}), 428

    corners = [tuple(point) for point in corners]
    hg = create_hg(corners, center)

    content = request.get_json(silent=True)
    match_id = content['match_id']
    time_number = content['time_number']
    points = content['points']

    for point in points:
        top_point = top_projection(point, center, hg)
        scaled_top_point = scale(top_point)

        # ОТПРАВИТЬ ТОЧКУ В БД

    return jsonify({'Successful': True}), 202


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0')


