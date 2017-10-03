import cv2
import numpy as np


# Перевод полярных координат в декартовы
def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y


# Функция искажения
def distortfun(r, k):
    return r * (1 + k * r)


# Параметр масштабирования
def brcor(k, center, R):
    return 1 / (1 + k * (min(center) / R) ** 2)


# Пересчет точки из кривого кадра в прямой
def recalc(point, center, k=-0.305):
    x = point[0]
    y = point[1]

    # Center - точка центра на кадре
    xc = center[0]
    yc = center[1]

    xu, yu = x - xc, y - yc
    theta = np.arctan2(yu, xu)
    s2 = xu / np.cos(theta)
    R = np.sqrt(xc ** 2 + yc ** 2)
    br = brcor(k, center, R)
    s = s2 / (R * br)
    r = (-1 + np.sqrt(np.abs(1 + 4 * k * s))) / (2 * k)
    xt, yt = pol2cart(r * R, theta)

    x_corrected = xt + xc
    y_corrected = yt + yc
    return np.array([int(round(x_corrected)), int(round(y_corrected))])


def create_hg_undist(side_view_corners):
    top_view_corners = np.array([[65, 60], [585, 60], [585, 395], [65, 395]])
    return cv2.findHomography(side_view_corners, top_view_corners)[0]


def create_hg(corners_points, center):
    undist_corner_points = [recalc(point, center) for point in corners_points]
    return create_hg_undist(np.copy(undist_corner_points))


def top_projection(point, center, hg_matrix):
    x, y = point[0], point[1]
    upoint = recalc((x, y), center)
    point = np.matrix(np.zeros(shape=(1, 3)))
    point[0, :] = np.array([upoint[0], upoint[1], 1], dtype="float32")
    top_point = hg_matrix * point.T
    x = int(top_point[0] / float(top_point[2]))
    y = int(top_point[1] / float(top_point[2]))
    return np.array([x, y])


def scale(point, width=105, height=68):
    point = np.array([point[0] - 65, point[1] - 60])
    dimension_pixels = np.array([520, 335])
    dimension_meters = np.array([width, height])
    scaled_point = point / dimension_pixels * dimension_meters
    normalized_point = np.array([scaled_point[0] - width / 2, height - scaled_point[1]])
    return np.around(normalized_point, decimals=1)


def get_bias(bottom_point, center, hg):
    top_point = top_projection(bottom_point, center, hg)
    return scale(top_point)


def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]))


def speed(time1, time2, distance2):
    t = time2 - time1
    return distance2 / t if t > 0 else 0.0


def acceleration(time1, speed1, time2, speed2):
    t = time2 - time1
    return (speed2 - speed1) / t if t > 0 else 0.0
