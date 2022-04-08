import time
from threading import Thread
from typing import Optional


class ObjectDetector:
    def __init__(self):
        # https://tfhub.dev/tensorflow/lite-model/efficientdet/lite0/detection/metadata/1?lite-format=tflite
        self.__detection_process: Optional[Thread] = None

    def run(self, _object_name: str):
        self.__detection_process = Thread(target=self.__detection_thread)  # , args=(recognizer, microphone))
        self.__detection_process.start()
        # self.__detection_thread()

    def __detection_thread(self):
        import cv2

        camera_id = 0
        width = 640
        height = 480
        counter, fps = 0, 0
        start_time = time.time()

        cap = cv2.VideoCapture(camera_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Visualization parameters
        row_size = 20  # pixels
        left_margin = 24  # pixels
        text_color = (0, 0, 255)  # red
        font_size = 1
        font_thickness = 1
        fps_avg_frame_count = 10

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print('ERROR: Unable to read from webcam. Please verify your webcam settings.')
                break

            counter += 1
            # image = cv2.flip(image, 1)

            # Calculate the FPS
            if counter % fps_avg_frame_count == 0:
                end_time = time.time()
                fps = fps_avg_frame_count / (end_time - start_time)
                start_time = time.time()

            # Show the FPS
            fps_text = 'FPS = {:.1f}'.format(fps)
            text_location = (left_margin, row_size)
            cv2.putText(image, fps_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                        font_size, text_color, font_thickness)

            if cv2.waitKey(1) == 27:
                break
            cv2.imshow('object_detector', image)

        cap.release()
        cv2.destroyAllWindows()
