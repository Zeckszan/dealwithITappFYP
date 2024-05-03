import cv2
import numpy as np

class HomogeneousBgDetector():
    def __init__(self):
        pass

    def detect_objects(self, frame):
        # cv2.imshow("b4 ",frame)

        # cv2.imshow("after ",frame)
        # Convert Image to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        Gaussian = cv2.GaussianBlur(gray, (7, 7), 0)
        mask = cv2.adaptiveThreshold(Gaussian, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 19, 5)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                           (5, 5))  # Size(1, 1) in C++ corresponds to (3, 3) in Python

        kernel2 = np.ones((7, 7), np.uint8)
        mormask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel2)
        
        # Find contours
        contours, _ = cv2.findContours(mormask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        objects_contours = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 2000:
                #cnt = cv2.approxPolyDP(cnt, 0.03*cv2.arcLength(cnt, True), True)
                objects_contours.append(cnt)

        return objects_contours

