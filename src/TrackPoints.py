import numpy as np


class Point:

    def __init__(self, id, match_id, team_id, player_id, period, video_part, pos_x, pos_y,
                 time):
        self.id = id
        self.match_id = match_id
        self.team_id = team_id
        self.player_id = player_id
        self.period = period
        self.video_part = video_part
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.time = time

    def __repr__(self):
        return "id = " + str(self.id) + " match_id = " + str(self.match_id)


class TrackPoints:

    def __init__(self, resp):
        self.list = np.ndarray((len(resp['data']),), dtype=np.object)
        i = 0
        for data in resp['data']:
            point = Point(data['id'],
                          data['match_id'],
                          data['team_id'],
                          data['player_id'],
                          data['period'],
                          data['video_part'],
                          data['pos_x'],
                          data['pos_y'],
                          data['video_second']
                          )
            self.list[i] = point
            i += 1
