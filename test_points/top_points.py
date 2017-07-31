import cv2
import numpy as np
from recalculation import create_hg, top_projection, scale

fields = np.empty((0, 2), dtype='int')

center = np.array([2048, 650])
# center = np.array([1920, 1080])
corners = [(1047, 298), (3020, 319), (4069, 808), (-5, 740)]
# corners = [(950, 850), (2745, 865), (3800, 1365), (-50, 1370)]

hg = create_hg(corners, center)


def create_field(img, dx=0.2, dy=0.3):
    img = cv2.resize(img, (0, 0), fx=dx, fy=dy)

    def field_click(event, x, y, flags, param):
        global fields
        if event == cv2.EVENT_LBUTTONUP:
            fields = np.vstack((fields, np.array([x, y])))
            print(x / dx, y / dy)
            cv2.circle(img, (x, y), 2, (255, 0, 0), 5)
            top_point = top_projection(np.array([x / dx, y / dy]), center, hg)
            scaled_top_point = scale(top_point)
            cv2.putText(img, 'x = ' + str(scaled_top_point[0]) + ';y = ' + str(scaled_top_point[1]), (x, y - 20), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255))

    win_name = 'Highlight soccer field'
    cv2.namedWindow(win_name)
    cv2.setMouseCallback(win_name, field_click, None)
    while 1:
        cv2.imshow(win_name, img)
        if cv2.waitKey(20) & 0xFF == 27:
            break
    cv2.destroyAllWindows()
    x_min, y_min = np.amin(fields, axis=0)
    x_max, y_max = np.amax(fields, axis=0)
    # return path.Path(fields / [dx, dy]), (int(x_min / dx), int(x_max / dx)), (int(y_min / dy), int(y_max / dy))
    return np.vstack((fields, fields[0])), (int(x_min / dx), int(x_max / dx)), (int(y_min / dy), int(y_max / dy))

path_to_image = 'output.png'
img = cv2.imread(path_to_image)
# cv2.circle(img, corners[0], 2, (255, 0, 0), 30)
# cv2.circle(img, corners[1], 2, (255, 0, 0), 30)
# cv2.circle(img, corners[2], 2, (255, 0, 0), 30)
# cv2.circle(img, corners[3], 2, (255, 0, 0), 30)
# img = cv2.resize(img, (0, 0), fx=0.2, fy=0.3)
# cv2.imshow('a', img)
# cv2.waitKey(0)

field_polygon, (x_min, x_max), (y_min, y_max) = create_field(img)
