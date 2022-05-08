import os
import numpy as np
import cv2

from src.gui.core.gui import GUI


class DepthEstimator:
    def __init__(self, gui: GUI):
        self.__gui = gui

        # model_name = "model-f6b98070.onnx" # MiDaS v2.1 Large
        model_name = "model-small.onnx"  # MiDaS v2.1 Small

        self.__model = cv2.dnn.readNet(os.path.join(os.path.dirname(os.path.realpath(__file__)), model_name))

        if self.__model.empty():
            print("Could not load the neural net! - Check path")

        self.__model.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        self.__model.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

    def close(self):
        pass

    def estimate(self, image: np.ndarray) -> np.ndarray:
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # MiDaS v2.1 Large ( Scale : 1 / 255, Size : 384 x 384, Mean Subtraction : ( 123.675, 116.28, 103.53 ), Channels Order : RGB )
        # blob = cv2.dnn.blobFromImage(img, 1/255., (384,384), (123.675, 116.28, 103.53), True, False)

        # MiDaS v2.1 Small ( Scale : 1 / 255, Size : 256 x 256, Mean Subtraction : ( 123.675, 116.28, 103.53 ), Channels Order : RGB )
        blob = cv2.dnn.blobFromImage(img, 1/255., (256,256), (123.675, 116.28, 103.53), True, False)

        self.__model.setInput(blob)
        output = self.__model.forward()

        output = output[0, :, :]

        img_height, img_width = img.shape[:2]
        output = cv2.resize(output, (img_width, img_height))

        # Normalize the output
        output = cv2.normalize(output, None, 0, 1, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_32F)

        # return np.stack((output*255,)*3, axis=-1)
        return cv2.cvtColor(output * 255, cv2.COLOR_GRAY2BGR)
