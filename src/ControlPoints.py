import numpy as np
import datetime
import sys


class Point:

    def __init__(self, id, c_mileage_datatype, video_timecode, data_value_int_1, data_value_int_2):
        self.id = id
        self.c_mileage_datatype = c_mileage_datatype
        self.video_timecode = video_timecode
        self.x = data_value_int_1
        self.y = data_value_int_2

    def __repr__(self):
        return "x = " + str(self.x) + " y = " + str(self.y) +\
               " c_mileage_datatype = " + str(self.c_mileage_datatype) + " timecode = " + str(self.video_timecode)


class ControlPoints:

    def __init__(self, resp):
        self.list = np.ndarray((len(resp['data']),), dtype=np.object)
        i = 0
        for data in resp['data']:
            point = Point(data['id'],
                          data['c_mileage_datatype'],
                          data['video_timecode'],
                          data['data_value_int_1'],
                          data['data_value_int_2'])
            self.list[i] = point
            i += 1

    def near_time(self, timecode):
        diff = sys.maxsize
        res_time = ""
        time = datetime.datetime.strptime(timecode, "%H:%M:%S")
        for p in self.list:
            p_t = datetime.datetime.strptime(p.video_timecode, "%H:%M:%S")
            curr_diff = time - p_t
            if 0 < curr_diff.seconds < diff:
                diff = curr_diff.seconds
                res_time = p.video_timecode

        return res_time

    def near_time_by_sec(self, sec):
        timecode = str(datetime.timedelta(seconds=sec))
        return self.near_time(timecode)


    def get_points(self, sec):
        n_t = self.near_time_by_sec(sec)
        top_left = list(filter(lambda p: p.video_timecode == n_t and p.c_mileage_datatype == 2, self.list))[0]
        top_left = np.array([top_left.x, top_left.y])

        top_right = list(filter(lambda p: p.video_timecode == n_t and p.c_mileage_datatype == 3, self.list))[0]
        top_right = np.array([top_right.x, top_right.y])

        bottom_right = list(filter(lambda p: p.video_timecode == n_t and p.c_mileage_datatype == 9, self.list))[0]
        bottom_right = np.array([bottom_right.x, bottom_right.y])

        bottom_left = list(filter(lambda p: p.video_timecode == n_t and p.c_mileage_datatype == 8, self.list))[0]
        bottom_left = np.array([bottom_left.x, bottom_left.y])

        intersection_bottom = list(filter(lambda p: p.video_timecode == n_t and p.c_mileage_datatype == 4, self.list))[0]
        intersection_bottom = np.array([intersection_bottom.x, intersection_bottom.y])

        pic_size = list(filter(lambda p: p.c_mileage_datatype == 10, self.list))[0]
        center = np.array([pic_size.x / 2, pic_size.y / 2])

        return np.array([top_left, top_right, bottom_right, bottom_left, intersection_bottom, center])

