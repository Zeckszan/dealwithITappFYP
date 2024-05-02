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
        # resized_frame = cv2.resize(mask, (400, 400))
        # cv2.imshow("g ", resized_frame)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                                           (5, 5))  # Size(1, 1) in C++ corresponds to (3, 3) in Python

        kernel2 = np.ones((7, 7), np.uint8)
        mormask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel2)

        # Apply morphological opening operation
        # blueMask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Apply morphological closing operation
        # blueMask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Create a Mask with adaptive threshold


        # opening_kernel = np.ones((7, 7), np.uint8)
        # opening = cv2.morphologyEx(mask, cv2.MORPH_OPEN, opening_kernel)
        # resized_frame = cv2.resize(mormask, (400, 400))
        # cv2.imshow("j ", resized_frame)
        #
        # # Apply morphological closing to fill small gaps
        # closing_kernel = np.ones((7, 7), np.uint8)
        # closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, closing_kernel)
        # resized_frame = cv2.resize(closing, (300, 300))
        # cv2.imshow("g ", resized_frame)
        # Find contours
        contours, _ = cv2.findContours(mormask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #cv2.imshow("mask", mask)
        objects_contours = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 2000:
                #cnt = cv2.approxPolyDP(cnt, 0.03*cv2.arcLength(cnt, True), True)
                objects_contours.append(cnt)

        return objects_contours

    # def get_objects_rect(self):
    #     box = cv2.boxPoints(rect)  # cv2.boxPoints(rect) for OpenCV 3.x
    #     box = np.int0(box)
# frame = cv2.imread("photoApp/img.jpg")
# HomogeneousBgDetector().detect_objects(frame)
