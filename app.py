import numpy as np
import requests

from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
from flask_httpauth import HTTPBasicAuth

import config
from recalculation import create_hg, top_projection, scale, get_bias
from recalculation import distance, speed, acceleration
from src.ControlPoints import ControlPoints
from src.StreamPoints import StreamPoints
from src.TrackPoints import TrackPoints

import logging
from logging.handlers import RotatingFileHandler

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


@app.route('/api/v1.0/test_auth', methods=['POST'])
@auth.login_required
def test_auth():
    return make_response(jsonify({'Successful': True}), 200)


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'Successful': False, 'error': 'Unauthorized access'}), 401)


@app.route('/api/v1.0/save_points', methods=['POST'])
@auth.login_required
def save_points():
    if not request.json:
        abort(400)

    content = request.get_json(silent=True)
    app.logger.info(str(content))

    try:
        action = content['action']
        match_id = content['match_id']
        half = content['half']
        team = content['team_id']
        player_id = content['player_id']
        points = content['points']
        video_seconds = content['video_seconds']
        video_part = content['video_part']
        user_id = content['user_id']
        c_mileage_event = content['c_mileage_event']
        player2_id = content['player2_id']

    except KeyError:
        return jsonify({'Successful: ':  False, 'Error: ': 'One of the parameters was missed'}), 400

    if len(points) != len(video_seconds):
        return jsonify({'Successful: ':  False, 'Error: ': 'The dimensions of arrays points '
                                                           'and video_seconds do not correspond'}), 428
    i = 0
    for point in points:
        _ = requests.post('http://service.instatfootball.com/ws.php',
                          json={'server': "instatfootball.com",
                                'login': config.login,
                                'pass': config.password,
                                'proc': 'iud_f_mileage_data3',
                                'params':
                                    {
                                        '@action': [action, 'in'],
                                        '@match_id': [match_id, 'in'],
                                        '@team_id': [team, 'in'],
                                        '@player_id': [player_id, 'in'],
                                        '@video_part': [video_part, 'in'],
                                        '@period': [half, 'in'],
                                        '@video_second': [video_seconds[i], 'in'],
                                        '@pos_x': [point[0], 'in'],
                                        '@pos_y': [point[1], 'in'],
                                        '@user_id': [user_id, 'in'],
                                        '@c_mileage_event': [c_mileage_event, 'in'],
                                        '@player2_id': [player2_id, 'in']

                                    }
                                })
        i += 1

    return jsonify({'Successful': True}), 202


def get_rp(con_points, p):
    try:
        cp = con_points.get_points(p.time)
    except IndexError:
        return jsonify({'Successful: ': False, 'Error: ': 'Control points were not found'}), 428

    corners = cp[:4]
    corners = [tuple(point) for point in corners]
    center = cp[-1]
    origin = cp[4]
    hg = create_hg(corners, center)

    point = np.array([p.pos_x, p.pos_y])
    top_point = top_projection(point, center, hg)
    scaled_top_point = scale(top_point)

    biases = get_bias(origin, center, hg)
    r_p = scaled_top_point - biases

    return r_p


@app.route('/api/v1.0/calc_track', methods=['POST'])
@auth.login_required
def calc_track():
    if not request.json:
        abort(400)

    content = request.get_json(silent=True)
    try:
        match_id = content['match_id']
        player_id = content['player_id']
        weight = content['player_weight']
        user_id = content['user_id']

    except KeyError:
        return jsonify({'Successful: ':  False, 'Error: ': 'One of the parameters was missed'}), 400

    r = requests.post('http://service.instatfootball.com/ws.php',
                      json={'server': "instatfootball.com",
                            'login': config.login,
                            'pass': config.password,
                            'proc': 'ask_f_mileage_data3',
                            'params':
                                {
                                    '@match_id': [match_id, 'in'],
                                    '@player_id': [player_id, 'in']
                                }
                            })

    response = r.json()
    if not response['data']:
        return jsonify({'Successful: ': False, 'Error: ': 'Match data is not found in the database'}), 428

    points = StreamPoints(response)

    r = requests.post('http://service.instatfootball.com/ws.php',
                      json={'server': "instatfootball.com",
                            'login': config.login,
                            'pass': config.password,
                            'proc': 'ask_f_mileage_matchdata_2',
                            'params':
                                {
                                    '@match_id': [match_id, 'in']
                                }
                            })
    response = r.json()
    if not response['data']:
        return jsonify({'Successful: ': False, 'Error: ': 'Control points of the match '
                                                          'is not found in the database'}), 428

    con_points = ControlPoints(response)

    tmp_speed = 0
    for i in range(1, len(points.list)):
        p_prev = points.list[i - 1]
        p = points.list[i]

        rp_prev = get_rp(con_points, p_prev)
        rp = get_rp(con_points, p)

        d = distance(rp_prev, rp)
        s = speed(p_prev.time, p.time, d)
        acc = acceleration(p_prev.time, tmp_speed, p.time, s)

        tmp_speed = s

        weight = weight if weight > 0 else 75

        energy_cost = (155.4 * np.power(np.tan(1.570797 - np.arctan(9.8 / acc)), 5)
                       - 30.4 * np.power(np.tan(1.570797 - np.arctan(9.8 / acc)), 4)
                       - 43.3 * np.power(np.tan(1.570797 - np.arctan(9.8 / acc)), 3)
                       + 46.3 * np.power(np.tan(1.570797 - np.arctan(9.8 / acc)), 2)
                       + 19.5 * (np.tan(1.570797 - np.arctan(9.8 / acc))) + 3.6)\
                      * np.sqrt(np.power(acc, 2) + 96.04) / 9.8 * 1.29

        estimated_energy = energy_cost * d / 4.1868 * weight
        metabolic_power = energy_cost * s
        _ = requests.post('http://service.instatfootball.com/ws.php',
                          json={'server': "instatfootball.com",
                                'login': config.login,
                                'pass': config.password,
                                'proc': 'iud_f_mileage_data3',
                                'params':
                                    {
                                        '@action': [2, 'in'],
                                        '@id': [p.id, 'in'],
                                        '@match_id': [match_id, 'in'],
                                        '@team_id': [p.team_id, 'in'],
                                        '@player_id': [player_id, 'in'],
                                        '@period': [p.period, 'in'],
                                        '@video_part': [p.video_part, 'in'],
                                        '@video_second': [p.time, 'in'],
                                        '@pos_x': [p.pos_x, 'in'],
                                        '@pos_y': [p.pos_y, 'in'],
                                        '@pos_x_recalc': [rp[0], 'in'],
                                        '@pos_y_recalc': [rp[1], 'in'],
                                        '@distance': [d, 'in'],
                                        '@speed': [s, 'in'],
                                        '@acceleration': [acc, 'in'],
                                        '@metabolic_power': [metabolic_power, 'in'],
                                        '@energy_cost': [energy_cost, 'in'],
                                        '@estimated_energy': [estimated_energy, 'in'],
                                        '@c_mileage_event': [p.c_mileage_event, 'in'],
                                        '@player2_id': [p.player2_id, 'in'],
                                        '@user_id': [user_id, 'in']
                                    }
                                })

    return jsonify({'Successful': True}), 202


@app.route('/api/v1.0/get_track', methods=['GET'])
@auth.login_required
def get_track():

    try:
        match_id = request.args.get('match_id')
        player_id = request.args.get('player_id')
        half = request.args.get('half')
    except KeyError:
        return jsonify({'Successful: ':  False, 'Error: ': 'One of the parameters was missed'}), 400

    r = requests.post('http://service.instatfootball.com/ws.php',
                      json={'server': "instatfootball.com",
                            'login': config.login,
                            'pass': config.password,
                            'proc': 'ask_f_mileage_data3',
                            'params':
                                {
                                    '@match_id': [match_id, 'in'],
                                    '@player_id': [player_id, 'in'],
                                }
                            })
    response = r.json()
    if not response['data']:
        return jsonify({'Successful: ': False, 'Error: ': 'Match data is not found in the database'}), 428

    points = TrackPoints(response)
    data = {'Successful': True, 'points': []}
    for p in points.list:
        time, pos_x, pos_y = p.time, p.pos_x, p.pos_y
        if p.period != int(half):
            continue
        data['points'].append({'x': pos_x, 'y': pos_y, 'time': time})

    return jsonify(data), 200


@app.route('/api/v1.0/remove_points', methods=['POST'])
@auth.login_required
def remove():
    if not request.json:
        abort(400)

    content = request.get_json(silent=True)
    try:
        match_id = content['match_id']
        player_id = content['player_id']
        video_seconds = content['video_seconds']

    except KeyError:
        return jsonify({'Successful: ':  False, 'Error: ': 'One of the parameters was missed'}), 400

    r = requests.post('http://service.instatfootball.com/ws.php',
                      json={'server': "instatfootball.com",
                            'login': config.login,
                            'pass': config.password,
                            'proc': 'ask_f_mileage_data3',
                            'params':
                                {
                                    '@match_id': [match_id, 'in'],
                                    '@player_id': [player_id, 'in'],
                                }
                            })
    response = r.json()
    if not response['data']:
        return jsonify({'Successful: ': False, 'Error: ': 'Match data is not found in the database'}), 428

    points = TrackPoints(response)
    for p in points.list:
        if p.time in video_seconds:
            _ = requests.post('http://service.instatfootball.com/ws.php',
                              json={'server': "instatfootball.com",
                                    'login': config.login,
                                    'pass': config.password,
                                    'proc': 'iud_f_mileage_data3',
                                    'params':
                                        {
                                            '@action': [3, 'in'],
                                            '@match_id': [match_id, 'in'],
                                            '@id': [p.id, 'in']
                                        }
                                    })
    return jsonify({'Successful': True}), 202


@app.route('/api/v1.0/change_points', methods=['POST'])
@auth.login_required
def change():
    if not request.json:
        abort(400)

    content = request.get_json(silent=True)
    try:
        match_id = content['match_id']
        player_id = content['player_id']
        video_seconds = content['video_seconds']
        points = content['points']
        user_id = content['user_id']

    except KeyError:
        return jsonify({'Successful: ':  False, 'Error: ': 'One of the parameters was missed'}), 400

    r = requests.post('http://service.instatfootball.com/ws.php',
                      json={'server': "instatfootball.com",
                            'login': config.login,
                            'pass': config.password,
                            'proc': 'ask_f_mileage_data3',
                            'params':
                                {
                                    '@match_id': [match_id, 'in'],
                                    '@player_id': [player_id, 'in'],
                                }
                            })
    response = r.json()
    if not response['data']:
        return jsonify({'Successful: ': False, 'Error: ': 'Match data is not found in the database'}), 428

    pts = StreamPoints(response)
    for p in pts.list:
        if p.time in video_seconds:
            i = video_seconds.index(p.time)
            new_point = points[i]
            _ = requests.post('http://service.instatfootball.com/ws.php',
                              json={'server': "instatfootball.com",
                                    'login': config.login,
                                    'pass': config.password,
                                    'proc': 'iud_f_mileage_data3',
                                    'params':
                                        {
                                            '@action': [2, 'in'],
                                            '@id': [p.id, 'in'],
                                            '@match_id': [match_id, 'in'],
                                            '@team_id': [p.team_id, 'in'],
                                            '@player_id': [player_id, 'in'],
                                            '@video_part': [p.video_part, 'in'],
                                            '@period': [p.period, 'in'],
                                            '@video_second': [p.time, 'in'],
                                            '@pos_x': [new_point[0], 'in'],
                                            '@pos_y': [new_point[1], 'in'],
                                            '@user_id': [user_id, 'in'],
                                            '@c_mileage_event': [p.c_mileage_event, 'in'],
                                            '@player2_id': [p.player2_id, 'in']

                                        }
                                    })
    return jsonify({'Successful': True}), 202


@app.route('/api/v1.0/clear', methods=['POST'])
@auth.login_required
def clear():
    if not request.json:
        abort(400)

    content = request.get_json(silent=True)
    try:
        match_id = content['match_id']
        player_id = content['player_id']

    except KeyError:
        return jsonify({'Successful: ':  False, 'Error: ': 'One of the parameters was missed'}), 400

    r = requests.post('http://service.instatfootball.com/ws.php',
                      json={'server': "instatfootball.com",
                            'login': config.login,
                            'pass': config.password,
                            'proc': 'ask_f_mileage_data3',
                            'params':
                                {
                                    '@match_id': [match_id, 'in'],
                                    '@player_id': [player_id, 'in'],
                                }
                            })
    response = r.json()
    if not response['data']:
        return jsonify({'Successful: ': False, 'Error: ': 'Match data is not found in the database'}), 428

    pts = TrackPoints(response)
    for p in pts.list:
        _ = requests.post('http://service.instatfootball.com/ws.php',
                          json={'server': "instatfootball.com",
                                'login': config.login,
                                'pass': config.password,
                                'proc': 'iud_f_mileage_data3',
                                'params':
                                    {
                                        '@action': [3, 'in'],
                                        '@match_id': [match_id, 'in'],
                                        '@id': [p.id, 'in']
                                    }
                                })
    return jsonify({'Successful': True}), 202


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    handler = RotatingFileHandler('python.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0')
    # app.run()
