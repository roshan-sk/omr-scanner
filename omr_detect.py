import cv2
import numpy as np


def get_contours(edged):
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 100000:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        if len(approx) == 4:
            return approx

    return None


def reorder(points):
    points = points.reshape((4, 2))
    new_points = np.zeros((4, 1, 2), dtype=np.int32)

    add = points.sum(1)
    new_points[0] = points[np.argmin(add)]
    new_points[3] = points[np.argmax(add)]

    diff = np.diff(points, axis=1)
    new_points[1] = points[np.argmin(diff)]
    new_points[2] = points[np.argmax(diff)]

    return new_points


def warp_image(image, points):
    points = reorder(points)

    pts1 = np.float32(points)
    pts2 = np.float32([[0, 0], [800, 0], [0, 1200], [800, 1200]])

    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    warped = cv2.warpPerspective(image, matrix, (800, 1200))

    return warped


def crop_answer_area(image):
    h, w = image.shape[:2]

    TOP = int(h * 0.33)
    BOTTOM = int(h * 0.16)
    LEFT = int(w * 0.16)
    RIGHT = int(w * 0.06)

    return image[TOP:h - BOTTOM, LEFT:w - RIGHT]


def preprocess_and_warp(image):
    image = cv2.resize(image, (800, 1200))

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)

    contour = get_contours(edged)

    if contour is None:
        return image

    area = cv2.contourArea(contour)
    if area < 300000:
        return image

    return warp_image(image, contour)


def split_into_columns(bubble_only, num_cols=5):
    h, w = bubble_only.shape[:2]
    col_width = w // num_cols

    columns = []
    for i in range(num_cols):
        x1 = i * col_width
        x2 = (i + 1) * col_width
        columns.append(bubble_only[:, x1:x2])

    return columns


def manual_crop_column(col_img):
    h, w = col_img.shape[:2]

    LEFT_MARGIN = 50
    cropped = col_img[:, LEFT_MARGIN:w]

    top_crop = int(h * 0.03)
    return cropped[top_crop:h, :]


def get_threshold(cropped):
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)

    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV,
        21, 5
    )


def detect_rows(thresh):
    row_sum = np.sum(thresh, axis=1)
    max_val = np.max(row_sum)

    if max_val == 0:
        return []

    row_sum = row_sum / max_val

    rows = []
    in_row = False

    for i in range(len(row_sum)):
        if row_sum[i] > 0.2 and not in_row:
            start = i
            in_row = True
        elif row_sum[i] < 0.2 and in_row:
            end = i
            rows.append((start, end))
            in_row = False

    final_rows = [(s, e) for (s, e) in rows if (e - s) > 15]

    return sorted(final_rows, key=lambda x: x[0])


def detect_answers(thresh, rows):
    answers = []

    for (start, end) in rows:
        row_img = thresh[start:end, :]

        h, w = row_img.shape
        margin = int(w * 0.05)
        row_img = row_img[:, margin:w - margin]

        h, w = row_img.shape
        option_width = w // 4

        scores = []

        for i in range(4):
            x1 = i * option_width
            x2 = (i + 1) * option_width

            option = row_img[
                int(h*0.3):int(h*0.7),
                x1 + int(option_width*0.3): x2 - int(option_width*0.3)
            ]

            scores.append(cv2.countNonZero(option))

        sorted_scores = sorted(scores, reverse=True)

        max_val = sorted_scores[0]
        second_val = sorted_scores[1]
        third_val = sorted_scores[2]

        spread = max_val - third_val

        if spread < 25:
            answers.append(-1)
        elif abs(max_val - second_val) < 20 and max_val > 1.3 * third_val:
            answers.append(-2)
        else:
            answers.append(np.argmax(scores))

    return answers


def process_column(col_img, c_indx):
    thresh = get_threshold(col_img)
    rows = detect_rows(thresh)
    return detect_answers(thresh, rows)