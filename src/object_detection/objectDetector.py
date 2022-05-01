import json
import time
import os
import uuid

import numpy as np
from threading import Thread
from typing import Optional, List, NamedTuple, Callable
from tflite_support import metadata

# pylint: disable=g-import-not-at-top
try:
    # Import TFLite interpreter from tflite_runtime package if it's available.
    from tflite_runtime.interpreter import Interpreter
    from tflite_runtime.interpreter import load_delegate
except ImportError:
    # If not, fallback to use the TFLite interpreter from the full TF package.
    import tensorflow as tf

    Interpreter = tf.lite.Interpreter
    load_delegate = tf.lite.experimental.load_delegate


# pylint: enable=g-import-not-at-top


class Rect(NamedTuple):
    """A rectangle in 2D space."""
    left: float
    top: float
    right: float
    bottom: float


class Category(NamedTuple):
    """A result of a classification task."""
    label: str
    score: float
    index: int


class Detection(NamedTuple):
    """A detected object as the result of an ObjectDetector."""
    bounding_box: Rect
    categories: List[Category]


# def edgetpu_lib_name():
#   """Returns the library name of EdgeTPU in the current platform."""
#   return {
#       'Darwin': 'libedgetpu.1.dylib',
#       'Linux': 'libedgetpu.so.1',
#       'Windows': 'edgetpu.dll',
#   }.get(platform.system(), None)

class ObjectDetector:
    def __init__(self, on_detection_callback: Callable[[tuple[float, float], float], None]):
        self.__id = uuid.uuid4().hex

        self.__on_detection_callback = on_detection_callback

        self.__is_running = False
        self.__last_frames: List[any] = []
        self.__max_frames = 60
        self.__camera_preview_process: Optional[Thread] = None
        self.__detection_process: Optional[Thread] = None
        self.__detections: List[Detection] = []

        label_deny_list: Optional[List[str]] = None
        label_allow_list: Optional[List[str]] = None

        self.__options = dict({
            'num_threads': 4,
            'score_threshold': 0.3,
            'max_results': 3,
            'enable_edgetpu': False,
            'label_deny_list': label_deny_list,
            'label_allow_list': label_allow_list,
        })

        self.__MARGIN = 10  # pixels
        self.__ROW_SIZE = 10  # pixels
        self.__FONT_SIZE = 1
        self.__FONT_THICKNESS = 1
        self.__TEXT_COLOR = (64, 64, 255)  # red

        # https://tfhub.dev/tensorflow/lite-model/efficientdet/lite0/detection/metadata/1?lite-format=tflite
        model_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'efficientdet_lite0.tflite')

        displayer = metadata.MetadataDisplayer.with_model_file(model_path)
        model_metadata = json.loads(displayer.get_metadata_json())
        process_units = model_metadata['subgraph_metadata'][0]['input_tensor_metadata'][0]['process_units']
        self.__mean = 127.5
        self.__std = 127.5
        for option in process_units:
            if option['options_type'] == 'NormalizationOptions':
                self.__mean = option['options']['mean'][0]
                self.__std = option['options']['std'][0]
        # self.__mean = mean
        # self.__std = std

        # Load label list from metadata.
        file_name = displayer.get_packed_associated_file_list()[0]
        label_map_file = displayer.get_associated_file_buffer(file_name).decode()
        self.__label_list = list(filter(len, label_map_file.splitlines()))
        # print("Labels:", self.__label_list) # 'cat', 'dog', 'horse', 'sheep', 'cow', 'bear', 'zebra', 'teddy bear'...

        # Initialize TFLite model.
        # if options.enable_edgetpu: #TODO: check it out after getting hands on Coral USB accelerator with Google Edge TPU
        #   if edgetpu_lib_name() is None:
        #     raise OSError("The current OS isn't supported by Coral EdgeTPU.")
        #   interpreter = Interpreter(
        #       model_path=model_path,
        #       experimental_delegates=[load_delegate(edgetpu_lib_name())],
        #       num_threads=options.num_threads)
        # else:
        self.__interpreter = Interpreter(model_path=model_path, num_threads=self.__options["num_threads"])

        self.__interpreter.allocate_tensors()
        input_detail = self.__interpreter.get_input_details()[0]

        # From TensorFlow 2.6, the order of the outputs become undefined.
        # Therefore, we need to sort the tensor indices of TFLite outputs and to know
        # exactly the meaning of each output tensor. For example, if
        # output indices are [601, 599, 598, 600], tensor names and indices aligned
        # are:
        #   - location: 598
        #   - category: 599
        #   - score: 600
        #   - detection_count: 601
        # because of the op's ports of TFLITE_DETECTION_POST_PROCESS
        # (https://github.com/tensorflow/tensorflow/blob/a4fe268ea084e7d323133ed7b986e0ae259a2bc7/tensorflow/lite/kernels/detection_postprocess.cc#L47-L50).
        sorted_output_indices = sorted(
            [output['index'] for output in self.__interpreter.get_output_details()])
        self.__output_indices = {
            'OUTPUT_LOCATION_NAME': sorted_output_indices[0],
            'OUTPUT_CATEGORY_NAME': sorted_output_indices[1],
            'OUTPUT_SCORE_NAME': sorted_output_indices[2],
            'OUTPUT_NUMBER_NAME': sorted_output_indices[3],
        }

        self.__input_size = input_detail['shape'][2], input_detail['shape'][1]
        self.__is_quantized_input = input_detail['dtype'] == np.uint8

    def id(self):
        return self.__id

    def run(self, _object_name: str):
        self.__is_running = True

        self.__camera_preview_process = Thread(target=self.__camera_preview_thread)  # , args=(recognizer, microphone))
        self.__camera_preview_process.daemon = True
        self.__camera_preview_process.start()

        self.__detection_process = Thread(target=self.__detection_thread)  # , args=(recognizer, microphone))
        self.__detection_process.daemon = True
        self.__detection_process.start()

    def __detect(self, input_image: np.ndarray) -> List[Detection]:
        image_height, image_width, _ = input_image.shape

        input_tensor = self.__preprocess(input_image)

        self.__set_input_tensor(input_tensor)
        self.__interpreter.invoke()

        # Get all output details
        boxes = self.__get_output_tensor('OUTPUT_LOCATION_NAME')
        classes = self.__get_output_tensor('OUTPUT_CATEGORY_NAME')
        scores = self.__get_output_tensor('OUTPUT_SCORE_NAME')
        count = int(self.__get_output_tensor('OUTPUT_NUMBER_NAME'))

        return self.__postprocess(boxes, classes, scores, count, image_width, image_height)

    def __detection_thread(self):
        while self.__is_running:
            if len(self.__last_frames) == 0:
                continue
            image = self.__last_frames[len(self.__last_frames) - 1]
            self.__detections = self.__detect(image)
            # print("Detections count:", len(self.__detections))
            self.__visualize(image, self.__detections)

            for detection in self.__detections:
                if detection.categories[0].label in (
                        'cat', 'dog', 'horse', 'sheep', 'cow', 'bear', 'zebra', 'teddy bear', 'bottle'):  # , 'person'
                    image_height, image_width, _ = image.shape
                    center = (
                        ((detection.bounding_box.left + detection.bounding_box.right) / 2) / image_width * 2.0 - 1.0,
                        ((detection.bounding_box.top + detection.bounding_box.bottom) / 2) / image_height * 2.0 - 1.0
                    )
                    normalized_area = abs(
                        detection.bounding_box.right - detection.bounding_box.left) / image_width * abs(
                        detection.bounding_box.bottom - detection.bounding_box.top) / image_height
                    self.__on_detection_callback(center, normalized_area)

    def __camera_preview_thread(self):
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

        while cap.isOpened() and self.__is_running:
            success, image = cap.read()
            if not success:
                print('ERROR: Unable to read from webcam. Please verify your webcam settings.')
                break

            counter += 1
            # image = cv2.flip(image, 1)

            self.__last_frames.append(image)
            if len(self.__last_frames) > self.__max_frames:
                self.__last_frames.pop(0)

            # Run object detection estimation using the model.
            # detections = self.__detect(image)
            # print("Detections count:", len(detections))
            self.__visualize(image, self.__detections)

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
            # noinspection PyBroadException
            try:
                cv2.imshow('Object detector', image)
            except BaseException:
                pass

        cap.release()
        cv2.destroyAllWindows()
        self.__is_running = False

    def __preprocess(self, input_image: np.ndarray) -> np.ndarray:
        import cv2

        # Resize the input
        input_tensor = cv2.resize(input_image, self.__input_size)

        # Normalize the input if it's a float model (aka. not quantized)
        if not self.__is_quantized_input:
            input_tensor = (np.float32(input_tensor) - self.__mean) / self.__std

        # Add batch dimension
        input_tensor = np.expand_dims(input_tensor, axis=0)

        return input_tensor

    def __set_input_tensor(self, image):
        """Sets the input tensor."""
        tensor_index = self.__interpreter.get_input_details()[0]['index']
        input_tensor = self.__interpreter.tensor(tensor_index)()[0]
        input_tensor[:, :] = image

    def __get_output_tensor(self, name: str):
        """Returns the output tensor at the given index."""
        output_index = self.__output_indices[name]
        tensor = np.squeeze(self.__interpreter.get_tensor(output_index))
        return tensor

    def __postprocess(self, boxes: np.ndarray, classes: np.ndarray, scores: np.ndarray, count: int, image_width: int,
                      image_height: int) -> List[Detection]:
        results: List[Detection] = []

        # Parse the model output into a list of Detection entities.
        for i in range(count):
            if scores[i] >= self.__options["score_threshold"]:
                y_min, x_min, y_max, x_max = boxes[i]
                bounding_box = Rect(
                    top=int(y_min * image_height),
                    left=int(x_min * image_width),
                    bottom=int(y_max * image_height),
                    right=int(x_max * image_width))
                class_id = int(classes[i])
                category = Category(score=scores[i], label=str(self.__label_list[class_id]), index=class_id)
                result = Detection(bounding_box=bounding_box, categories=[category])
                results.append(result)

        # Sort detection results by score ascending
        sorted_results = sorted(results, key=lambda detection: detection.categories[0].score, reverse=True)

        # Filter out detections in deny list
        filtered_results = sorted_results
        if self.__options["label_deny_list"] is not None:
            filtered_results = list(
                filter(lambda detection: detection.categories[0].label not in self.__options["label_deny_list"],
                       filtered_results))

        # Keep only detections in allow list
        if self.__options["label_allow_list"] is not None:
            filtered_results = list(
                filter(lambda detection: detection.categories[0].label in self.__options["label_allow_list"],
                       filtered_results))

        # Only return maximum of max_results detection.
        if self.__options["max_results"] > 0:
            result_count = min(len(filtered_results), self.__options["max_results"])
            filtered_results = filtered_results[:result_count]

        return filtered_results

    def __visualize(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray:
        import cv2

        for detection in detections:
            # Draw bounding_box
            start_point = detection.bounding_box.left, detection.bounding_box.top
            end_point = detection.bounding_box.right, detection.bounding_box.bottom
            cv2.rectangle(image, start_point, end_point, self.__TEXT_COLOR, 3)

            # Draw center point
            center = (
                int((detection.bounding_box.left + detection.bounding_box.right) / 2),
                int((detection.bounding_box.top + detection.bounding_box.bottom) / 2)
            )
            cv2.circle(image, center, 4, self.__TEXT_COLOR, -1)

            # Draw label and score
            category = detection.categories[0]
            class_name = category.label
            probability = round(category.score, 2)
            result_text = class_name + ' (' + str(probability) + ')'
            text_location = (self.__MARGIN + detection.bounding_box.left,
                             self.__MARGIN + self.__ROW_SIZE + detection.bounding_box.top)
            cv2.putText(image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                        self.__FONT_SIZE, self.__TEXT_COLOR, self.__FONT_THICKNESS)

        return image

    def stop(self):
        self.__is_running = False
        if self.__detection_process is not None:
            self.__detection_process.join()
        if self.__camera_preview_process is not None:
            self.__camera_preview_process.join()
