import numpy as np


class Point:

    def __init__(self, id, match_id, team_id, player_id, period, video_part, pos_x, pos_y,
                 pos_x_recalc, pos_y_recalc, time, c_mileage_event, player2_id, speed):
        self.id = id
        self.match_id = match_id
        self.team_id = team_id
        self.player_id = player_id
        self.period = period
        self.video_part = video_part
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.pos_x_recalc = pos_x_recalc
        self.pos_y_recalc = pos_y_recalc
        self.time = time
        self.speed = speed
        self.c_mileage_event = c_mileage_event
        self.player2_id = player2_id


    def __repr__(self):
        return "id = " + str(self.id) + " match_id = " + str(self.match_id) +\
               " pos_x_recalc = " + str(self.pos_x_recalc) + " pos_y_recalc = " + str(self.pos_y_recalc)


class StreamPoints:

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
                          float(data['pos_x_recalc']),
                          float(data['pos_y_recalc']),
                          data['video_second'],
                          data['c_mileage_event_id'],
                          data['player2_id'],
                          data['speed'])
            self.list[i] = point
            i += 1

    @staticmethod
    def distance(p1, p2):
        return np.sqrt((p1.pos_x_recalc - p2.pos_x_recalc) ** 2 + (p1.pos_y_recalc - p2.pos_y_recalc))

    @staticmethod
    def speed(p1, p2):
        t = p2.time - p1.time
        return p2.distance / t if t > 0 else 0.0

    @staticmethod
    def acceleration(p1, p2):
        t = p2.time - p1.time
        return (p2.speed - p1.speed) / t if t > 0 else 0.0
